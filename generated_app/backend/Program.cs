using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Cors.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("https://todo.example.com", "http://localhost:3000")
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

builder.Services.AddDbContext<TodoDb>(options =>
    options.UseSqlite("Data Source=todos.db"));

builder.Services.AddScoped<TodoService>();

var app = builder.Build();

app.UseHttpsRedirection();
app.UseCors("AllowFrontend");

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<TodoDb>();
    db.Database.Migrate();
}

app.MapGet("/health", () => Results.Ok(new { status = "healthy" }))
    .WithName("Health")
    .WithOpenApi();

app.MapGet("/todos", GetAllTodos)
    .WithName("GetAllTodos")
    .WithOpenApi();

app.MapGet("/todos/{id}", GetTodoById)
    .WithName("GetTodoById")
    .WithOpenApi();

app.MapPost("/todos", CreateTodo)
    .WithName("CreateTodo")
    .WithOpenApi();

app.MapPut("/todos/{id}", UpdateTodo)
    .WithName("UpdateTodo")
    .WithOpenApi();

app.MapDelete("/todos/{id}", DeleteTodo)
    .WithName("DeleteTodo")
    .WithOpenApi();

app.MapPatch("/todos/{id}/toggle", ToggleTodo)
    .WithName("ToggleTodo")
    .WithOpenApi();

app.Run();

async Task<IResult> GetAllTodos(TodoDb db)
{
    try
    {
        var todos = await db.Todos
            .OrderByDescending(t => t.CreatedAt)
            .ToListAsync();
        return Results.Ok(todos);
    }
    catch (Exception ex)
    {
        return Results.StatusCode(500);
    }
}

async Task<IResult> GetTodoById(int id, TodoDb db)
{
    try
    {
        var todo = await db.Todos.FindAsync(id);
        if (todo == null)
            return Results.NotFound();
        return Results.Ok(todo);
    }
    catch (Exception ex)
    {
        return Results.StatusCode(500);
    }
}

async Task<IResult> CreateTodo(CreateTodoRequest request, TodoDb db)
{
    if (string.IsNullOrWhiteSpace(request.Title))
        return Results.BadRequest(new { error = "Title is required" });

    if (request.Title.Length > 255)
        return Results.BadRequest(new { error = "Title must not exceed 255 characters" });

    try
    {
        var todo = new Todo
        {
            Title = request.Title.Trim(),
            IsCompleted = false,
            CreatedAt = DateTime.UtcNow
        };

        db.Todos.Add(todo);
        await db.SaveChangesAsync();

        return Results.Created($"/todos/{todo.Id}", todo);
    }
    catch (Exception ex)
    {
        return Results.StatusCode(500);
    }
}

async Task<IResult> UpdateTodo(int id, UpdateTodoRequest request, TodoDb db)
{
    if (string.IsNullOrWhiteSpace(request.Title))
        return Results.BadRequest(new { error = "Title is required" });

    if (request.Title.Length > 255)
        return Results.BadRequest(new { error = "Title must not exceed 255 characters" });

    try
    {
        var todo = await db.Todos.FindAsync(id);
        if (todo == null)
            return Results.NotFound();

        todo.Title = request.Title.Trim();
        todo.UpdatedAt = DateTime.UtcNow;

        db.Todos.Update(todo);
        await db.SaveChangesAsync();

        return Results.Ok(todo);
    }
    catch (Exception ex)
    {
        return Results.StatusCode(500);
    }
}

async Task<IResult> DeleteTodo(int id, TodoDb db)
{
    try
    {
        var todo = await db.Todos.FindAsync(id);
        if (todo == null)
            return Results.NotFound();

        db.Todos.Remove(todo);
        await db.SaveChangesAsync();

        return Results.NoContent();
    }
    catch (Exception ex)
    {
        return Results.StatusCode(500);
    }
}

async Task<IResult> ToggleTodo(int id, TodoDb db)
{
    try
    {
        var todo = await db.Todos.FindAsync(id);
        if (todo == null)
            return Results.NotFound();

        todo.IsCompleted = !todo.IsCompleted;
        todo.UpdatedAt = DateTime.UtcNow;

        db.Todos.Update(todo);
        await db.SaveChangesAsync();

        return Results.Ok(todo);
    }
    catch (Exception ex)
    {
        return Results.StatusCode(500);
    }
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
            entity.Property(e => e.Id).ValueGeneratedOnAdd();
            entity.Property(e => e.Title).IsRequired().HasMaxLength(255);
            entity.Property(e => e.IsCompleted).HasDefaultValue(false);
            entity.Property(e => e.CreatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");
            entity.HasIndex(e => e.CreatedAt).HasName("IX_Todo_CreatedAt");
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

    public async Task<List<Todo>> GetAllTodosAsync()
    {
        return await _db.Todos.OrderByDescending(t => t.CreatedAt).ToListAsync();
    }

    public async Task<Todo?> GetTodoByIdAsync(int id)
    {
        return await _db.Todos.FindAsync(id);
    }

    public async Task<Todo> CreateTodoAsync(string title)
    {
        var todo = new Todo
        {
            Title = title.Trim(),
            IsCompleted = false,
            CreatedAt = DateTime.UtcNow
        };

        _db.Todos.Add(todo);
        await _db.SaveChangesAsync();
        return todo;
    }

    public async Task<Todo?> UpdateTodoAsync(int id, string title)
    {
        var todo = await _db.Todos.FindAsync(id);
        if (todo == null)
            return null;

        todo.Title = title.Trim();
        todo.UpdatedAt = DateTime.UtcNow;
        _db.Todos.Update(todo);
        await _db.SaveChangesAsync();
        return todo;
    }

    public async Task<bool> DeleteTodoAsync(int id)
    {
        var todo = await _db.Todos.FindAsync(id);
        if (todo == null)
            return false;

        _db.Todos.Remove(todo);
        await _db.SaveChangesAsync();
        return true;
    }

    public async Task<Todo?> ToggleTodoAsync(int id)
    {
        var todo = await _db.Todos.FindAsync(id);
        if (todo == null)
            return null;

        todo.IsCompleted = !todo.IsCompleted;
        todo.UpdatedAt = DateTime.UtcNow;
        _db.Todos.Update(todo);
        await _db.SaveChangesAsync();
        return todo;
    }
}

public class CreateTodoRequest
{
    public string Title { get; set; } = string.Empty;
}

public class UpdateTodoRequest
{
    public string Title { get; set; } = string.Empty;
}