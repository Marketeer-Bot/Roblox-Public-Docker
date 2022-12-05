# Should be inputted as strings. We'll take care of the rest.
productRoles={}

# Example:
exampleProductRoles={"productId1":"roleNameCaseSensitive","productId2":"roleNameCaseSensitive"}

# Don't edit anything beyond this:
async def getRole(product):
    product = str(product)
    try:
        product=productRoles[product]
    except:
        return None
    return product