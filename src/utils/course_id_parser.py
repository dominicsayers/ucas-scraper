class CourseIdParser:
    """Handles parsing and validation of course IDs"""

    @staticmethod
    def parse(unparsed_id: str) -> str:
        """
        Parse course ID from either a URL or direct ID.

        Args:
            unparsed_id: Raw course ID or URL containing course ID

        Returns:
            Extracted course ID
        """
        if unparsed_id.lower().startswith("http"):
            return unparsed_id.split("/")[-1].split("?")[0]
        return unparsed_id
