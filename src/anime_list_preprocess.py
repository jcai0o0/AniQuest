import pandas as pd
from pathlib import Path


def combine_anime_set():
    df1 = pd.read_csv(Path(Path(__file__).parent, "data/", "anime-dataset-2023.csv"))
    df2 = pd.read_csv(Path(Path(__file__).parent, "data/", "AnimeList.csv"))

    df_anime_1 = df1[['Name', 'Score', 'Genres', 'Synopsis', 'Producers', 'Studios', 'Rank', 'Popularity', 'Favorites', 'Scored By', 'Members', 'Image URL']]
    df_anime_1 = df_anime_1[df_anime_1['Synopsis'] != 'No description available for this anime.']

    df_anime_2 = df2[['anime_id', 'title', 'score', 'scored_by', 'rank', 'popularity', 'members', 'favorites', 'genre']]

    df_final = pd.merge(df_anime_1, df_anime_2, left_on='Name', right_on='title')
    print(df_final.shape)
    df_final.to_csv(Path(Path(__file__).parent, "data/", "final_anime_list.csv"), index=False)
    return


if __name__=='__main__':
    # combine_anime_set()
    df = pd.read_csv(Path(Path(__file__).parent, "data/", "final_anime_list.csv"))
    print(df.shape)

