---
CoinsCopper: 0
CoinsSiler: 0
CoinsGold: 0
CoinsPlatinum: 0
PartySize: 1
---

# Enter Currency Amount

| Type     | Input                         | Copper                       | Silver                      | Gold                       | Platinum                   |
| -------- | ----------------------------- | ---------------------------- | --------------------------- | -------------------------- | -------------------------- |
| Copper   | `INPUT[number:CoinsCopper]`   | `VIEW[{CoinsCopper}]`        | `VIEW[{CoinsCopper}/10]`    | `VIEW[{CoinsCopper}/100]`  | `VIEW[{CoinsCopper}/1000]` |
| Silver   | `INPUT[number:CoinsSiler]`    | `VIEW[{CoinsSiler}*10]`      | `VIEW[{CoinsSiler}]`        | `VIEW[{CoinsSiler}/10]`    | `VIEW[{CoinsSiler}/100]`   |
| Gold     | `INPUT[number:CoinsGold]`     | `VIEW[{CoinsGold}*100]`      | `VIEW[{CoinsGold}*10]`      | `VIEW[{CoinsGold}]`        | `VIEW[{CoinsGold}/10]`     |
| Platinum | `INPUT[number:CoinsPlatinum]` | `VIEW[{CoinsPlatinum}*1000]` | `VIEW[{CoinsPlatinum}*100]` | `VIEW[{CoinsPlatinum}*10]` | `VIEW[{CoinsPlatinum}]`    |

# Total Converted Value

Party Size: `INPUT[number:PartySize]`  

| Type     | Total                                                                                                          | Total Per Player                                                                                                           |
| -------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Copper   | `VIEW[{CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000)]`          | `VIEW[({CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000))/{PartySize}]`        |
| Silver   | `VIEW[(({CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000))/10)]`   | `VIEW[(({CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000))/10)/{PartySize}]`   |
| Gold     | `VIEW[(({CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000))/100)]`  | `VIEW[(({CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000))/100)/{PartySize}]`  |
| Platinum | `VIEW[(({CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000))/1000)]` | `VIEW[(({CoinsCopper}+({CoinsSiler}*10)+({CoinsGold}*100)+({CoinsPlatinum}*1000))/1000)/{PartySize}]` | 
