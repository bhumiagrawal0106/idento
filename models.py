
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True, nullable=False)
    name = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='student')  # 'admin' or 'student'
    is_active = Column(Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def init_db(uri):
    engine = create_engine(uri, echo=False, future=True)
    Base.metadata.create_all(engine)
    return engine

