from v3.acquirers.course import CourseAcquirer


def main() -> None:
    course = CourseAcquirer()
    course.process("508f8040-1309-e5cb-ff57-c4ff9c902ed3")  # Example UCAS course ID


if __name__ == "__main__":
    main()
