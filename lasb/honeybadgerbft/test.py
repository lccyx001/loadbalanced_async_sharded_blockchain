
def a(j):
    print("a",j)

def b(a):
    print("b0")
    a(1)
    print("b")

if __name__ == "__main__":
    b(a)