from sqlalchemy import Integer, Column, String, ForeignKey, ARRAY, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    hashed_password = Column(String)
    about = Column(String)
    profile_pic = Column(String)

    experiences = relationship("Experiences", back_populates="experienceOwner")
    projects = relationship("Projects", back_populates="projectsOwner")
    courses = relationship("Courses", back_populates="coursesOwner")


class Courses(Base):
    __tablename__ = "courses"

    id = Column(Integer,  primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    start_at = Column(String)
    end_at = Column(String)
    pic = Column(String)
    institution = Column(String)
    link = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    coursesOwner = relationship("Users", back_populates="courses")


class Experiences(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    name_company = Column(String)
    start_at = Column(String)
    end_at = Column(String)
    description = Column(String)
    role = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_my_current_work = Column(Boolean, default=False)

    experienceOwner = relationship("Users", back_populates="experiences")


class Projects(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    pre_description = Column(String)
    description = Column(String)
    # technologies = Column(ARRAY(String)) PARA USAR VOU TER QUE USAR O POSTGRES SQL PAR TAL, FAZER ISSO MAIS TARDE OU BUSCAR OUTRA ALTERNATIVA
    year = Column(Integer)
    image = Column(String)
    state = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))

    projectsOwner = relationship("Users", back_populates="projects")
