def backup_modes(delivery_modes: list[str], blocked_mode: str) -> list[str]:
    return [mode for mode in delivery_modes if mode != blocked_mode]
