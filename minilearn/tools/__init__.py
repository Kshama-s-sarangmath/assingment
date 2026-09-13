"""Registered Strands tools for the MiniLearn agent."""

from .enroll_in_course import enroll_in_course
from .get_course_details import get_course_details
from .get_my_enrollments import get_my_enrollments
from .get_popular_courses import get_popular_courses
from .search_courses import search_courses
from .unenroll_from_course import unenroll_from_course

ALL_TOOLS = [
    search_courses,
    get_course_details,
    enroll_in_course,
    unenroll_from_course,
    get_my_enrollments,
    get_popular_courses,
]
