from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

password = "123456"

hashed = pwd_context.hash(password)

print("HASH:")
print(hashed)

print()
print("VERIFY:")
print(pwd_context.verify(password, hashed))