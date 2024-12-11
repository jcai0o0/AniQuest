import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path


def data_preprocess():
    df_anime = pd.read_csv(Path(Path(__file__).parent, "data/", "final_anime_list.csv"))
    df_user = pd.read_csv(Path(Path(__file__).parent, "data/", "UserList.csv"))
    df_interaction = pd.read_csv(Path(Path(__file__).parent, "data/", "user_anime_list.csv"))

    data = df_interaction.merge(df_user, on='username', how='left')
    data = data.merge(df_anime, on='anime_id', how='left')

    # Encode users and anime
    user_ids = data["user_id"].astype("category").cat.codes
    anime_ids = data["anime_id"].astype("category").cat.codes

    # Add encoded IDs to the dataset
    data["user_id_encoded"] = user_ids
    data["anime_id_encoded"] = anime_ids

    data['genre'] = data['genre'].apply(lambda x: str(x) if not isinstance(x, str) else x)
    data = data[~data['genre'].apply(lambda x: isinstance(x, float) or pd.isna(x))]

    model = SentenceTransformer('all-MiniLM-L6-v2')
    data['genre_embedding'] = data['genre'].apply(lambda x: model.encode(x) if isinstance(x, str) else np.zeros(384))

    print(data.shape)
    data.to_csv(Path(Path(__file__).parent, "data/", "warm_rerank_data.csv"), index=False)

    return data


def user_item_matrix_preprocess():
    warm_rerank_data_path = Path(Path(__file__).parent, "data/", "warm_rerank_data.csv")
    data = pd.read_csv(warm_rerank_data_path)

    user_anime_matrix = data.pivot_table(index='user_id_encoded',
                                         columns='anime_id_encoded',
                                         values='my_score',
                                         aggfunc='mean').fillna(0)
    user_similarity_matrix = cosine_similarity(user_anime_matrix)
    user_similarities = pd.DataFrame(user_similarity_matrix,
                                     index=user_anime_matrix.index,
                                     columns=user_anime_matrix.index)

    print(user_similarities.shape)
    user_similarities.to_csv(Path(Path(__file__).parent, "data/", "user_similarities.csv"), index=False)

    return user_similarities.shape


def convert_embedding(embedding_str):
    try:
        # Split the string and convert each value to a float
        return np.array(list(map(float, embedding_str.split(','))))
    except ValueError:
        # Handle any invalid embedding format (optional)
        return np.zeros(384)  # Return a default zero array if invalid


def rank_anime_warm(userid, anime_list):
    """
    Rank anime for a given user based on genre similarity (70%) and collaborative filtering (30%).
    userid = 12  # Example user ID
    anime_list = ['Naruto', 'One Piece', 'Dragon Ball']
    data: matrix
    """
    data = pd.read_csv(Path(Path(__file__).parent, "data/", "warm_rerank_data.csv"))
    data['genre_embedding'] = data['genre_embedding'].apply(convert_embedding)
    # Step 3: load User-item similarity matrix
    user_similarities = pd.read_csv(Path(Path(__file__).parent, "data/", "user_similarities.csv"))

    # Step 1: Map anime names to IDs
    anime_name_to_id = data.set_index('title')['anime_id_encoded'].to_dict()

    missing_animes = [anime for anime in anime_list if anime not in anime_name_to_id]
    if missing_animes:
        print(f"Anime names not found in the dataset: {', '.join(missing_animes)}")
        # raise ValueError()

    # Filter out missing animes from anime_list
    anime_list_filtered = [anime for anime in anime_list if anime not in missing_animes]
    # Get the anime_ids for the filtered anime_list
    anime_ids = [anime_name_to_id[anime_name] for anime_name in anime_list_filtered]

    # Step 2: User's watching history
    user_data = data[data['user_id_encoded'] == userid]
    watched_animes = user_data[['anime_id_encoded', 'my_score']]

    # Step 4: Compute user's genre preference
    user_genre_embeddings = data[data['anime_id_encoded'].isin(watched_animes['anime_id_encoded'])]['genre_embedding'].tolist()
    user_genre_vector = (np.mean(user_genre_embeddings, axis=0) if user_genre_embeddings else np.zeros(384))

    # Step 5: Rank anime based on similarity and collaborative filtering
    anime_ranking = []
    for anime_id in anime_ids:
        # User's rating for the anime
        user_rating = user_data[user_data['anime_id_encoded'] == anime_id]['my_score'].values
        user_rating = user_rating[0] if user_rating.size > 0 else 0

        # Collaborative filtering (CF) score
        similar_users = data[data['anime_id_encoded'] == anime_id].copy()
        similar_users['similarity'] = similar_users['user_id_encoded'].apply(lambda x: user_similarities.iloc[userid, x])
        top_similar_users = similar_users[similar_users['my_score'] > 0].nlargest(3, 'similarity')
        cf_score = (np.average(top_similar_users['my_score'],
                               weights=top_similar_users['similarity']) if not top_similar_users.empty else 0)

        # If user's rating is 0, use CF score as a fallback
        if user_rating == 0:
            user_rating = cf_score

        # Genre similarity score
        anime_genre_vector = data.loc[data['anime_id_encoded'] == anime_id, 'genre_embedding'].values[0]
        genre_similarity = cosine_similarity([user_genre_vector], [anime_genre_vector])[0][0]

        # Final score (weighted combination)
        final_score = 0.7 * genre_similarity + 0.3 * user_rating
        anime_title = list(anime_name_to_id.keys())[list(anime_name_to_id.values()).index(anime_id)]
        anime_ranking.append((anime_title, final_score))

    # Sort by final score
    ranked_animes = sorted(anime_ranking, key=lambda x: x[1], reverse=True)
    return ranked_animes