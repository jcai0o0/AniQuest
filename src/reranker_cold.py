import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity

import ast



def rank_anime_by_query(query, anime_titles, anime_data, model, sentence_model):
    # Filter data by anime titles
    filtered_anime_data = anime_data[anime_data['title'].isin(anime_titles)].copy()

    # Features for static scoring
    features = ["score", "rank_normalized", "popularity_log", "favorites_log", "scored_by_log", "members_log"]

    # Predict static scores
    filtered_anime_features = filtered_anime_data[features]
    static_scores = model.predict(filtered_anime_features)

    # Add static scores to the DataFrame
    filtered_anime_data.loc[:, 'static_score'] = static_scores

    # Initialize SentenceTransformer model

    query_embedding = sentence_model.encode([query])

    # Function to parse embeddings
    def parse_embedding(embedding_str):
        if not isinstance(embedding_str, str) or embedding_str.strip() == "":
            return []
        try:
            return ast.literal_eval(embedding_str)
        except (ValueError, SyntaxError):
            cleaned_str = embedding_str.replace("\n", "").replace(" ", ",").replace(",,", ",").strip("[]")
            try:
                return [float(x) for x in cleaned_str.split(",") if x.strip() != ""]
            except ValueError:
                return []

    # Parse embeddings
    filtered_anime_data.loc[:, 'title_embedding'] = filtered_anime_data['title_embedding'].apply(parse_embedding)
    filtered_anime_data.loc[:, 'synopsis_embedding'] = filtered_anime_data['synopsis_embedding'].apply(parse_embedding)
    filtered_anime_data.loc[:, 'producers_embedding'] = filtered_anime_data['producers_embedding'].apply(parse_embedding)
    filtered_anime_data.loc[:, 'studios_embedding'] = filtered_anime_data['studios_embedding'].apply(parse_embedding)

    # Compute similarities
    filtered_anime_data.loc[:, 'title_similarity'] = filtered_anime_data['title_embedding'].apply(
        lambda x: cosine_similarity([x], query_embedding)[0][0] if len(x) > 0 else 0
    )

    filtered_anime_data.loc[:, 'synopsis_similarity'] = filtered_anime_data['synopsis_embedding'].apply(
        lambda x: cosine_similarity([x], query_embedding)[0][0] if len(x) > 0 else 0
    )

    filtered_anime_data.loc[:, 'producers_similarity'] = filtered_anime_data['producers_embedding'].apply(
        lambda x: cosine_similarity([x], query_embedding)[0][0] if len(x) > 0 else 0
    )

    filtered_anime_data.loc[:, 'studios_similarity'] = filtered_anime_data['studios_embedding'].apply(
        lambda x: cosine_similarity([x], query_embedding)[0][0] if len(x) > 0 else 0
    )

    # Calculate genre similarity
    genre_columns = [
        'Demons', 'Romance', 'Action', 'Adventure', 'Avant Garde', 'Award Winning',
        'Boys Love', 'Cars', 'Comedy', 'Dementia', 'Drama', 'Ecchi', 'Erotica',
        'Fantasy', 'Game', 'Girls Love', 'Gourmet', 'Harem', 'Hentai', 'Historical',
        'Horror', 'Josei', 'Kids', 'Magic', 'Martial Arts', 'Mecha', 'Military',
        'Music', 'Mystery', 'Parody', 'Police', 'Psychological', 'Samurai', 'School',
        'Sci-Fi', 'Seinen', 'Shoujo', 'Shounen', 'Slice of Life', 'Space', 'Sports',
        'Super Power', 'Supernatural', 'Suspense', 'Thriller', 'Vampire', 'Yaoi', 'Yuri'
    ]

    def calculate_genre_similarity(row):
        query_lower = query.lower()
        matches = sum([1 for genre in genre_columns if genre.lower() in query_lower and row.get(genre, 0) == 1])
        return matches / len(genre_columns)

    filtered_anime_data.loc[:, 'genre_similarity'] = filtered_anime_data.apply(calculate_genre_similarity, axis=1)

    # Calculate dynamic scores
    filtered_anime_data.loc[:, 'dynamic_score'] = (
        0.4 * filtered_anime_data['title_similarity'] +
        0.2 * filtered_anime_data['synopsis_similarity'] +
        0.1 * filtered_anime_data['producers_similarity'] +
        0.1 * filtered_anime_data['studios_similarity'] +
        0.2 * filtered_anime_data['genre_similarity']
    )

    # Calculate final scores
    filtered_anime_data.loc[:, 'final_score'] = (
        0.8 * filtered_anime_data['dynamic_score'] + 0.2 * filtered_anime_data['static_score']
    )

    # Sort by final score
    sorted_anime_data = filtered_anime_data.sort_values(by='final_score', ascending=False)

    # Convert to list of tuples
    ranked_anime_list = list(zip(sorted_anime_data['title'], sorted_anime_data['final_score']))

    return ranked_anime_list