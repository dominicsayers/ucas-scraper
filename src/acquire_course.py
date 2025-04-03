from v2.acquirers.course_acquirer import CourseAcquirer

url = "https://digital.ucas.com/coursedisplay/courses/508f8040-1309-e5cb-ff57-c4ff9c902ed3?academicYearId=2025"

course = CourseAcquirer(url)
course.process()
