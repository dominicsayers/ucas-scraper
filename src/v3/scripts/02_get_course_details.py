from v3.acquirers.course import CourseAcquirer
from v3.utils.file_handler import FileHandler
from v3.utils.config import Config


# This script acquires course details for a list of UCAS IDs
# It reads the UCAS IDs from a file and processes each ID to fetch course details.
config = Config()
file_handler = FileHandler("data")

list_file = f"course-ids-{config.course}.txt"
ucas_ids = file_handler.read_list([], list_file)

for ucas_id in ucas_ids:
    course = CourseAcquirer()
    course.process(ucas_id)
