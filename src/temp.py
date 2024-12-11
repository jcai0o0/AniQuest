from llm import query_chroma
from reranker_warm import rank_anime_warm


def integration_test(query, anime_count):
    anime_list = query_chroma(query=query, anime_count=anime_count)
    print(anime_list)

    new_list = rank_anime_warm(userid=12, anime_list=anime_list)
    print(new_list)

    return new_list


if __name__ == "__main__":
    my_query = "I want something like Demon Slayer, but with more romance and produced by Kyoto Animation"
    integration_test(query=my_query, anime_count=100)