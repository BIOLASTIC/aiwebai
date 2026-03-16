import typer
from rich.console import Console
from rich.table import Table
import asyncio
from sqlalchemy.future import select
from backend.app.db.engine import AsyncSessionLocal
from backend.app.auth.api_key_auth import generate_api_key, hash_key
from backend.app.db.models import User, ConsumerApiKey

app = typer.Typer(help="Gemini Unified Gateway CLI")
admin_app = typer.Typer(help="Admin commands")
app.add_typer(admin_app, name="admin")
console = Console()

@admin_app.command("create-api-key")
def create_api_key(
    email: str = typer.Option(..., prompt=True),
    label: str = typer.Option("default", help="Key label"),
):
    async def _create():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalars().first()
            if not user:
                console.print(f"[red]User {email} not found.[/red]")
                return
            
            api_key = generate_api_key()
            api_key_record = ConsumerApiKey(
                user_id=user.id,
                key_hash=hash_key(api_key),
                label=label,
                status="active"
            )
            session.add(api_key_record)
            await session.commit()
            console.print(f"[green]API Key created for {email}:[/green]")
            console.print(f"[bold cyan]{api_key}[/bold cyan]")
            console.print("[yellow]Save this key, it won't be shown again![/yellow]")
    
    asyncio.run(_create())

@admin_app.command("create-user")
def create_user(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    role: str = typer.Option("viewer", help="admin, operator, viewer, developer"),
):
    async def _create():
        async with AsyncSessionLocal() as session:
            user = User(
                email=email,
                password_hash=get_password_hash(password),
                role=role,
                status="active"
            )
            session.add(user)
            await session.commit()
            console.print(f"[green]User {email} created with role {role}.[/green]")
    
    asyncio.run(_create())

@admin_app.command("list-users")
def list_users():
    async def _list():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            table = Table(title="Gateway Users")
            table.add_column("ID", style="cyan")
            table.add_column("Email", style="magenta")
            table.add_column("Role", style="green")
            table.add_column("Status", style="yellow")
            
            for user in users:
                table.add_row(str(user.id), user.email, user.role, user.status)
            
            console.print(table)
    
    asyncio.run(_list())

if __name__ == "__main__":
    app()
