from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

password = "123456"

hashed_password = pwd_context.hash(password)

print("HASH PASSWORD:")
print(hashed_password)