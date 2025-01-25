from dataclasses import dataclass

@dataclass
class Course:
    subject: str
    course_num: str
    title: str
    crn: str
    status: str
    instructor: str
    campus: str
    dates: str
