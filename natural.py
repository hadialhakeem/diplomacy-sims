class PlayerSquare():
    def __init__(self, sum):
        self.sum = sum
        self.candidates = self.find_candidates()


    def find_candidates(self):
        candidates = set()
        for a in range(sum):
            for b in range(sum):
                if a**2 + b**2 == sum:
                    if a < b:
                        candidates.add((a, b))
                    else:
                        candidates.add((b, a))
                elif a**2 + b**2 > sum:
                    break
            if a**2 > sum:
                break
        return candidates
    
    def infer(self):
        



class PlayerSum():
    def __init__(self, sum):
        self.sum = sum
        self.candidates = self.find_candidates()

    def find_candidates(self):
        candidates = set()
        for a in range(sum):
            for b in range(sum):
                if a + b == sum:
                    if a < b:
                        candidates.add((a, b))
                    else:
                        candidates.add((b, a))
                elif a + b > sum:
                    break
            if a > sum:
                break
        return candidates


c = 8
d = 9

sum_of_squares = c*c + d*d
sum = c+d

pb = PlayerSquare(sum_of_squares)
pa = PlayerSum(sum)

while True:
    if len(pb.candidates) == 1:
        print("B: I know the numbers\n")
        break
    else:
        print("B: I do not know the numbers\n")

    if len(pa.candidates) == 1:
        print("A: I know the numbers\n")
        break
    else:
        print("A: I do not know the numbers\n")

    

    

