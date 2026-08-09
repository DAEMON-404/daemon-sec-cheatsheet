---
title: "Server Side Template Injection - ASP.NET"
topic: "Server Side Template Injection"
topicSlug: "server-side-template-injection"
sourcePath: "Server Side Template Injection/ASP.md"
sourceUrl: "https://github.com/swisskyrepo/PayloadsAllTheThings/blob/3bff425aca2b/Server%20Side%20Template%20Injection/ASP.md"
sha: "3bff425aca2b"
isReadme: false
---

# Server Side Template Injection - ASP.NET

> Server-Side Template Injection (SSTI)  is a class of vulnerabilities where an attacker can inject malicious input into a server-side template, causing the template engine to execute arbitrary code on the server. In the context of ASP.NET, SSTI can occur if user input is directly embedded into a template (such as Razor, ASPX, or other templating engines) without proper sanitization.

## Summary

- [ASP.NET Razor](#aspnet-razor)
    - [ASP.NET Razor - Basic Injection](#aspnet-razor---basic-injection)
    - [ASP.NET Razor - Command Execution](#aspnet-razor---command-execution)
- [References](#references)

## ASP.NET Razor

[Official website](https://docs.microsoft.com/en-us/aspnet/web-pages/overview/getting-started/introducing-razor-syntax-c)

> Razor is a markup syntax that lets you embed server-based code (Visual Basic and C#) into web pages.

### ASP.NET Razor - Basic Injection

```powershell
@(1+2)
```

### ASP.NET Razor - Command Execution

```csharp
@{
  // C# code
}
```

## References

- [Server-Side Template Injection (SSTI) in ASP.NET Razor - Clément Notin - April 15, 2020](https://web.archive.org/web/20240905143644/http://clement.notin.org/blog/2020/04/15/Server-Side-Template-Injection-(SSTI)-in-ASP.NET-Razor/)
