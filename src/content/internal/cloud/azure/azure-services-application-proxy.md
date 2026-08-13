---
title: "Azure Services - Application Proxy"
section: "Cloud"
sectionSlug: "cloud"
sourcePath: "docs/cloud/azure/azure-services-application-proxy.md"
sourceUrl: "https://github.com/swisskyrepo/InternalAllTheThings/blob/e891850d6bc6/docs/cloud/azure/azure-services-application-proxy.md"
sha: "e891850d6bc6"
isIndex: false
---

# Azure Services - Application Proxy

## Enumerate

* Enumerate applications that have Proxy

    ```powershell
    PS C:\Tools> Get-AzureADApplication -All $true | %{try{GetAzureADApplicationProxyApplication -ObjectId $_.ObjectID;$_.DisplayName;$_.ObjectID}catch{}}
    PS C:\Tools> Get-AzureADServicePrincipal -All $true | ?{$_.DisplayName -eq "Finance Management System"}

    PS C:\Tools> . C:\Tools\GetApplicationProxyAssignedUsersAndGroups.ps1
    PS C:\Tools> Get-ApplicationProxyAssignedUsersAndGroups -ObjectId <OBJECT-ID>
    ```

## References

* [Training - Attacking and Defending Azure Lab - Altered Security](https://www.alteredsecurity.com/azureadlab)
