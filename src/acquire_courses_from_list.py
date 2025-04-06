from v2.acquirers.course_acquirer import CourseAcquirer
from utils.output import Output

output = Output()
ucas_ids = output.read_list([], "ucas_ids.txt")

for ucas_id in ucas_ids:
    course = CourseAcquirer()
    course.process(ucas_id)
