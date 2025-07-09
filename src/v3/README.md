# ucas-scraper

Fetch course data from the UCAS (the UK Universities and Colleges Admissions Service) website

## Basic usage

From the command line

```shell
. .venv/bin/activate
COURSE=physics STUDY_YEAR=2026 DESTINATION=Undergraduate PREDICTED_GRADES=ABC,BBC,BCC python src/v3/scripts/01_course_search.py
```

This will generate a list of UCAS course IDs matching the search terms.
