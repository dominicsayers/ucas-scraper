# ucas-scraper

Fetch course data from the UCAS (the UK Universities and Colleges Admissions Service) website

## Basic usage

From the command line

```shell
. .venv/bin/activate
COURSE=physics STUDY_YEAR=2026 DESTINATION=Undergraduate PREDICTED_GRADES=ABC,BBC,BCC python src/v3/scripts/01_course_search.py
```

This will generate a list of UCAS course IDs matching the search terms (in `tmp/data/course_ids-physics.txt`).

Then you can acquire the course details for this list of courses like this:

```shell
COURSE=physics STUDY_YEAR=2026 DESTINATION=Undergraduate PREDICTED_GRADES=ABC,BBC,BCC python src/v3/scripts/02_get_course_details.py
```

This will scrape all the UCAS course pages, and the historical grades data, for all the course ids in the list and
update the data for all the course providers in `tmp/data/providers/<provider sort name>/<course title>`.
