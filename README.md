# ucas-scraper

Fetch course data from the UCAS (the UK Universities and Colleges Admissions Service) website

## Historical entry grades data

GET [https://services.ucas.com/historic-grades-api/loggedOut/e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e](https://services.ucas.com/historic-grades-api/loggedOut/e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e)

```json
{
    "courseId": "e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e",
    "results": [
        {
            "qualificationType": "A_level",
            "isAggregate": true,
            "mostCommonGrade": "ABB",
            "overallOfferRate": "19 in 20",
            "minimumGrade": "BBC",
            "maximumGrade": "A*A*A",
            "coursesIncluded": "This course and 18 other physics courses",
            "startYear": 2019,
            "endYear": 2023,
            "prominentQualification": false
        }
    ]
}
```

POST [https://services.ucas.com/historic-grades-api/loggedIn](https://services.ucas.com/historic-grades-api/loggedIn)

Payload:

```json
{"courseIds":["e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e"],"qualificationType":"A_level","grade":"AAB"}
```

Response:

```json
{
    "qualificationType": "A_level",
    "gradeProfile": "AAB",
    "results": [
        {
            "courseId": "e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e",
            "isAggregate": true,
            "confirmationRate": "100%"
        }
    ]
}
```

## Course details as data

Another potentially useful URL format: [https://services.ucas.com/search/api/v3/courses?courseDetailsRequest.coursePrimaryId=e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e&courseDetailsRequest.academicYearId=2025](https://services.ucas.com/search/api/v3/courses?courseDetailsRequest.coursePrimaryId=e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e&courseDetailsRequest.academicYearId=2025)
