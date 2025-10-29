def user_profile(request):
    """Context processor to safely provide user profile to all templates"""
    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
        except:
            pass  # Profile doesn't exist
    return {'user_profile_context': user_profile}

