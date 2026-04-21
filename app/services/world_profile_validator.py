class WorldProfileValidator:
    def validate(self, profile: dict) -> dict:
        errors = []
        if not isinstance(profile, dict):
            errors.append("profile_not_dict")
            return {"valid": False, "errors": errors}

        if "defaults" not in profile:
            errors.append("missing_defaults")
        if "maps" not in profile:
            errors.append("missing_maps")

        defaults = profile.get("defaults", {})
        if defaults and not isinstance(defaults, dict):
            errors.append("defaults_not_dict")

        maps = profile.get("maps", {})
        if maps and not isinstance(maps, dict):
            errors.append("maps_not_dict")

        return {"valid": len(errors) == 0, "errors": errors}


world_profile_validator = WorldProfileValidator()
