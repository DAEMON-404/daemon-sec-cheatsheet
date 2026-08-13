---
title: "Azure Services - Deployment Template"
section: "Cloud"
sectionSlug: "cloud"
sourcePath: "docs/cloud/azure/azure-services-deployment-template.md"
sourceUrl: "https://github.com/swisskyrepo/InternalAllTheThings/blob/e891850d6bc6/docs/cloud/azure/azure-services-deployment-template.md"
sha: "e891850d6bc6"
isIndex: false
---

# Azure Services - Deployment Template

* List the deployments

    ```powershell
    PS Az> Get-AzResourceGroup
    PS Az> Get-AzResourceGroupDeployment -ResourceGroupName SAP
    ```

* Export the deployment template

    ```ps1
    PS Az> Save-AzResourceGroupDeploymentTemplate -ResourceGroupName <RESOURCE GROUP> -DeploymentName <DEPLOYMENT NAME>
    
    # search for hardcoded password
    cat <DEPLOYMENT NAME>.json 
    cat <PATH TO .json FILE> | Select-String password
    ```

## References

* [Training - Attacking and Defending Azure Lab - Altered Security](https://www.alteredsecurity.com/azureadlab)
