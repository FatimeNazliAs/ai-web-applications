from fastapi import FastAPI,Body, Path, Query,HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from starlette import status




app=FastAPI()


class Course:
    id:int
    title:str
    instructor:str
    rating:int
    published_date:int

    def __init__(self,id:int,title:str,instructor:str,rating:int,published_date:int):
        self.id=id
        self.title=title
        self.instructor=instructor
        self.rating=rating
        self.published_date=published_date


class CourseRequest(BaseModel):
    id:Optional[int]=Field(description="The id of course, optional",default=None)
    title:str=Field(min_length=3,max_length=100)
    instructor:str=Field(min_length=3)
    rating:int=Field(gt=0,lt=6)
    published_date:int=Field(gte=1900,lte=2100)

    model_config = {
        "json_schema_extra":{
            "example":{
                "title":"My course",
                "instructor":"atil",
                "rating":5,
                "published_date":2020
            }
        }
    }


courses_db=[
    Course(1,"python","atil",5,2029),
    Course(2, "kotlin", "ahmet", 5, 2026),
    Course(3, "jenkins", "atil", 5, 2030),
    Course(4, "kubernetes", "zeynep", 2, 2036),
    Course(5, "machine learning", "fatma", 3, 2039),
    Course(6, "deep learning", "atlas", 1, 2029),

]

@app.get("/courses",status_code=status.HTTP_200_OK)
async def get_all_courses():
    return courses_db

@app.get("/courses/{course_id}",status_code=status.HTTP_200_OK)
async def get_course(course_id:int=Path(gt=0)): #gt=greater than, lt=less than
    for course in courses_db:
        if course.id==course_id:
            return course
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Course not found")


@app.get("/courses/",status_code=status.HTTP_200_OK)
async def get_courses_by_rating(course_rating:int=Query(gt=0,lt=6)): #gt=greater than, lt=less than
    courses_to_return=[] # there may be many courses with same rating
    for course in courses_db:
        if course.rating==course_rating:
            courses_to_return.append(course)
    return courses_to_return


@app.get("/courses/publish/",status_code=status.HTTP_200_OK)
async def get_courses_by_published_date(published_date:int=Query(gt=1700,lt=2040)): #gt=greater than, lt=less than
    courses_to_return=[] # there may be many courses with same published date
    for course in courses_db:
        if published_date==course.published_date:
            courses_to_return.append(course)
    return courses_to_return



@app.post("/create-course",status_code=status.HTTP_201_CREATED)
async def create_course(course_request:CourseRequest ):
    new_course=Course(**course_request.model_dump())
    courses_db.append(find_course_id(new_course))


def find_course_id(course:Course):
    course.id=1 if len(courses_db)==0 else courses_db[-1].id+1
    return course


@app.put("/courses/update_course",status_code=status.HTTP_204_NO_CONTENT)
async def update_course(course_request:CourseRequest):
    course_updated=False
    for i in range(len(courses_db)):
        if course_request.id==courses_db[i].id:
            courses_db[i]=course_request
            course_updated=True

    if not course_updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Course not found")
    print(course_updated)


@app.delete("/courses/delete/{course_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id:int=Path(gt=0)):
    course_deleted=False
    for i in range(len(courses_db)):
        if course_id == courses_db[i].id:
            courses_db.pop(i)
            course_deleted=True
            break

    if not course_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Course not found")

