from model import User,Blog,Comment
import db

db.create_engine(user='root',password='123456',database='myblog')

u = User(name = 'Test',email='fly_lxl@fixfox.com',password='123456',image='about:blank')

#u.insert()

print 'new user id:',u.id
u1 = User.find_first('where email =?','fly_lxl@fixfox.com')
print 'find user\'s name:',u1.name
