1. home_win leaks to strategies — strategies get the full row including the outcome. Drop it before passing.
2. Empty results have no columns — if strategy skips everything, Ben's metrics blow up. Return empty DataFrame with correct column names.
3. NaN odds corrupt all subsequent rows — skip rows with missing odds.
