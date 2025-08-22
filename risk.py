import random

attacker_wins = 0
defender_wins = 0

for _ in range(1_000_000):
    attacker = [random.randint(1,6) for _ in range(3)]
    defender = [random.randint(1,6) for _ in range(2)]

    attacker.sort(reverse=True)
    defender.sort(reverse=True)

    for i in range(2):
        if attacker[i] > defender[i]:
            attacker_wins += 1
        else:
            defender_wins += 1
    


attacker_win_percentage = attacker_wins / (attacker_wins + defender_wins)
defender_win_percentage = defender_wins / (attacker_wins + defender_wins)

print(f"Attacker win percentage: {attacker_win_percentage * 100:.2f}%")
print(f"Defender win percentage: {defender_win_percentage * 100:.2f}%")
print(f"Total games: {attacker_wins + defender_wins}")
print(f"Attacker wins: {attacker_wins}")
print(f"Defender wins: {defender_wins}")