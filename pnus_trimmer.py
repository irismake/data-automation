import ast

def trim_pnus(df):
    import ast

    updated_pnus = []
    non00_pnus = []

    for index, row in df.iterrows():
        try:
            pnus_raw = ast.literal_eval(row["pnus"])
            cleaned_pnus = []
            for pnu in pnus_raw:
                pnu_str = str(pnu)
                if pnu_str[-2:] == "00":
                    cleaned_pnus.append(int(pnu_str[:-2]))
                else:
                    non00_pnus.append(pnu_str)
                    cleaned_pnus.append(int(pnu_str))
            updated_pnus.append(cleaned_pnus)
        except Exception as e:
            non00_pnus.append(f"Error in row {index}: {e}")
            updated_pnus.append([])

    df["pnus"] = updated_pnus
    return df, non00_pnus
