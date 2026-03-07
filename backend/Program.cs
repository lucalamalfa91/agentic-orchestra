using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Cors.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<TodoDb>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection") ?? "Data Source=todos.db"));

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowedOrigins", policy =>
    {
        policy.WithOrigins(
            "https://todo-frontend.azurestaticapps.net",
            "http://localhost:3000")
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

builder.Services.AddScoped<TodoService>();

builder.Services.AddHealthChecks()
    .AddDbContextCheck<TodoDb>();

builder.Services.AddApplicationInsightsTelemetry();

var app = builder.Build();

app.UseHttpsRedirection();
app.UseCors("AllowedOrigins");

app.MapHealthChecks("/health");

var todoGroup = app.MapGroup("/todos")
    .WithName("Todos")
    .WithOpenApi();

todoGroup.MapGet("/", GetAllTodos)
    .WithName("GetAllTodos")
    .WithOpenApi()
    .Produces<List<TodoDto>>(StatusCodes.Status200OK);

todoGroup.MapGet("/{id}", GetTodoById)
    .WithName("GetTodoById")
    .WithOpenApi()
    .Produces<TodoDto>(StatusCodes.Status200OK)
    .Produces(StatusCodes.Status404NotFound);

todoGroup.MapPost("/", CreateTodo)
    .WithName("CreateTodo")
    .WithOpenApi()
    .Produces<TodoDto>(StatusCodes.Status201Created)
    .Produces(StatusCodes.Status400BadRequest);

todoGroup.MapPut("/{id}", UpdateTodo)
    .WithName("UpdateTodo")
    .WithOpenApi()
    .Produces<TodoDto>(StatusCodes.Status200OK)
    .Produces(StatusCodes.Status404NotFound)
    .Produces(StatusCodes.Status400BadRequest);

todoGroup.MapDelete("/{id}", DeleteTodo)
    .WithName("DeleteTodo")
    .WithOpenApi()
    .Produces(StatusCodes.Status204NoContent)
    .Produces(StatusCodes.Status404NotFound);

todoGroup.MapPatch("/{id}/toggle", ToggleTodo)
    .WithName("ToggleTodo")
    .WithOpenApi()
    .Produces<TodoDto>(StatusCodes.Status200OK)
    .Produces(StatusCodes.Status404NotFound);

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<TodoDb>();
    db.Database.Migrate();
}

app.Run();

async Task<IResult> GetAllTodos(TodoDb db)
{
    var todos = await db.Todos
        .OrderByDescending(t => t.CreatedAt)
        .Select(t => new TodoDto
        {
            Id = t.Id,
            Title = t.Title,
            IsCompleted = t.IsCompleted,
            CreatedAt = t.CreatedAt
        })
        .ToListAsync();

    return Results.Ok(todos);
}

async Task<IResult> GetTodoById(int id, TodoDb db)
{
    var todo = await db.Todos.FindAsync(id);

    if (todo == null)
        return Results.NotFound();

    var todoDto = new TodoDto
    {
        Id = todo.Id,
        Title = todo.Title,
        IsCompleted = todo.IsCompleted,
        CreatedAt = todo.CreatedAt
    };

    return Results.Ok(todoDto);
}

async Task<IResult> CreateTodo(CreateTodoRequest request, TodoDb db, TodoService service)
{
    if (string.IsNullOrWhiteSpace(request.Title) || request.Title.Length > 255)
        return Results.BadRequest(new { error = "Title is required and must be less than 255 characters" });

    var todo = new Todo
    {
        Title = request.Title.Trim(),
        IsCompleted = false,
        CreatedAt = DateTime.UtcNow
    };

    db.Todos.Add(todo);
    await db.SaveChangesAsync();

    var todoDto = new TodoDto
    {
        Id = todo.Id,
        Title = todo.Title,
        IsCompleted = todo.IsCompleted,
        CreatedAt = todo.CreatedAt
    };

    return Results.Created($"/todos/{todo.Id}", todoDto);
}

async Task<IResult> UpdateTodo(int id, UpdateTodoRequest request, TodoDb db)
{
    if (string.IsNullOrWhiteSpace(request.Title) || request.Title.Length > 255)
        return Results.BadRequest(new { error = "Title is required and must be less than 255 characters" });

    var todo = await db.Todos.FindAsync(id);

    if (todo == null)
        return Results.NotFound();

    todo.Title = request.Title.Trim();
    todo.IsCompleted = request.IsCompleted;
    todo.UpdatedAt = DateTime.UtcNow;

    await db.SaveChangesAsync();

    var todoDto = new TodoDto
    {
        Id = todo.Id,
        Title = todo.Title,
        IsCompleted = todo.IsCompleted,
        CreatedAt = todo.CreatedAt
    };

    return Results.Ok(todoDto);
}

async Task<IResult> DeleteTodo(int id, TodoDb db)
{
    var todo = await db.Todos.FindAsync(id);

    if (todo == null)
        return Results.NotFound();

    db.Todos.Remove(todo);
    await db.SaveChangesAsync();

    return Results.NoContent();
}

async Task<IResult> ToggleTodo(int id, TodoDb db)
{
    var todo = await db.Todos.FindAsync(id);

    if (todo == null)
        return Results.NotFound();

    todo.IsCompleted = !todo.IsCompleted;
    todo.UpdatedAt = DateTime.UtcNow;

    await db.SaveChangesAsync();

    var todoDto = new TodoDto
    {
        Id = todo.Id,
        Title = todo.Title,
        IsCompleted = todo.IsCompleted,
        CreatedAt = todo.CreatedAt
    };

    return Results.Ok(todoDto);
}

public class Todo
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public bool IsCompleted { get; set; } = false;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? UpdatedAt { get; set; }
}

public class TodoDb : DbContext
{
    public TodoDb(DbContextOptions<TodoDb> options) : base(options) { }

    public DbSet<Todo> Todos { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Todo>(entity =>
        {
            entity.HasKey(e => e.Id);

            entity.Property(e => e.Title)
                .IsRequired()
                .HasMaxLength(255);

            entity.Property(e => e.IsCompleted)
                .HasDefaultValue(false);

            entity.Property(e => e.CreatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP");

            entity.HasIndex(e => e.CreatedAt)
                .HasDatabaseName("IX_Todo_CreatedAt");

            entity.HasIndex(e => e.IsCompleted)
                .HasDatabaseName("IX_Todo_IsCompleted");
        });
    }
}

public class TodoService
{
    private readonly TodoDb _db;

    public TodoService(TodoDb db)
    {
        _db = db;
    }
}

public class TodoDto
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public bool IsCompleted { get; set; }
    public DateTime CreatedAt { get; set; }
}

public class CreateTodoRequest
{
    public string Title { get; set; } = string.Empty;
}

public class UpdateTodoRequest
{
    public string Title { get; set; } = string.Empty;
    public bool IsCompleted { get; set; }
}