1. home_win leaks to strategies — strategies get the full row including the outcome. Drop it before passing.
2. No CSV committed — Mya's generator is there but was never run. Execute it, commit test_games.csv so it works out of the box.
3. Empty results have no columns — if strategy skips everything, Ben's metrics blow up. Return empty DataFrame with correct column names.
4. NaN odds corrupt all subsequent rows — skip rows with missing odds.
