from v3.acquirers.course_search import SearchService


def main() -> None:
    search = SearchService()
    search.search_courses()


if __name__ == "__main__":
    main()
