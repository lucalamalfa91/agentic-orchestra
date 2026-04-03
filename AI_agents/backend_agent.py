# app-factory/AI_agents/backend_agent.py
from .ai_utils import call_ai, write_utf8, read_utf8, strip_markdown_fences

def main():
    print("=== STEP2: backend .NET ===")
    design = read_utf8("design.yaml")

    # Generate Program.cs
    prompt_program = f"""
    Design YAML:

    {design}

    Write the COMPLETE content of Program.cs file for a .NET 8 Minimal API based on the requirements above.

    MANDATORY REQUIREMENTS:
    1. Include ALL necessary using statements at the top:
       - using Microsoft.EntityFrameworkCore;
       - using Microsoft.OpenApi.Models;
       - using Microsoft.Extensions.Caching.Memory;
       - using System.Text.Json.Serialization;
       - Any other using statements needed

    2. Use WebApplication.CreateBuilder(args) (NOT WebApplicationBuilder.CreateBuilder)

    3. For JSON deserialization with snake_case API responses, use JsonPropertyName attributes:
       [JsonPropertyName("field_name")]
       public Type FieldName {{ get; set; }}

    4. Implement all endpoints specified in the design.yaml API section

    5. Add proper error handling with try-catch blocks

    6. If using external HTTP APIs, configure HttpClient properly

    7. Add CORS configuration for frontend access

    CRITICAL CONSTRAINTS:
    - DO NOT use markdown code blocks
    - DO NOT use language markers (no ```csharp, no ```)
    - Respond ONLY with C# code for Program.cs, ready to compile
    - Write ALL code, comments, variable names, strings in ENGLISH only
    - Use English for all entity names, properties, endpoints, error messages
    - Include ALL necessary using statements at the top
    """

    program_cs = call_ai(
        prompt_program,
        system_content="You are a senior .NET backend engineer. Produce only valid C# code with ALL necessary using statements. Write EVERYTHING in English only.",
        max_tokens=8000
    )
    program_cs = strip_markdown_fences(program_cs)
    write_utf8("backend/Program.cs", program_cs)

    # Generate .csproj file
    prompt_csproj = f"""
    Design YAML:

    {design}

    Generate a .csproj file for .NET 8 Web API with the necessary packages based on the design requirements.

    Include these packages at minimum:
    - Microsoft.AspNetCore.OpenApi (8.0.0)
    - Swashbuckle.AspNetCore (6.4.0)
    - Microsoft.Extensions.Caching.Memory (8.0.1 or later to avoid vulnerabilities)

    Add any other packages needed based on the design (Entity Framework, HttpClient, etc.)

    CRITICAL CONSTRAINTS:
    - DO NOT use markdown code blocks
    - Respond ONLY with valid XML for .csproj file
    - Use .NET 8.0 as target framework
    """

    csproj = call_ai(
        prompt_csproj,
        system_content="You are a .NET project configuration expert. Generate only valid .csproj XML."
    )
    csproj = strip_markdown_fences(csproj)
    write_utf8("backend/ComoWeather.csproj", csproj)

if __name__ == "__main__":
    main()
