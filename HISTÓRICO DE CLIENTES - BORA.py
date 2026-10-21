"""Histórico de Contatos de Clientes — Python + Tkinter + SQLite.
Execute no terminal do VS Code: python historico_clientes.py
"""
import sqlite3, tkinter as tk, csv, os, sys, subprocess
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
BANCO = PASTA / "historico_clientes.db"

def conectar():
    return sqlite3.connect(BANCO)

def criar_banco():
    with conectar() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT NOT NULL,
            cliente TEXT NOT NULL, codigo TEXT, telefone TEXT, projeto TEXT,
            canal TEXT, assunto TEXT, relato TEXT NOT NULL, providencia TEXT,
            responsavel TEXT, anexos TEXT DEFAULT '')""")
        colunas = [x[1] for x in db.execute("PRAGMA table_info(contatos)")]
        if "anexos" not in colunas:
            db.execute("ALTER TABLE contatos ADD COLUMN anexos TEXT DEFAULT ''")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Histórico de Contatos de Clientes")
        self.geometry("1200x790")
        self.minsize(950, 650)
        self.configure(bg="#F3F5F2")
        self.logo = None
        self.arquivos_anexados = []
        self.nome = tk.StringVar()
        self.codigo = tk.StringVar()
        self.telefone = tk.StringVar()
        self.projeto = tk.StringVar(value="21")
        self.canal = tk.StringVar(value="WhatsApp")
        self.assunto = tk.StringVar(value="Cobrança")
        self.responsavel = tk.StringVar()
        self.busca = tk.StringVar()
        self.estilo()
        self.interface()
        self.listar()

    def estilo(self):
        st = ttk.Style(self)
        try: st.theme_use("clam")
        except tk.TclError: pass
        st.configure("TLabel", background="#F3F6F7", font=("Segoe UI", 10))
        st.configure("TButton", font=("Segoe UI", 10), padding=5)
        st.configure("Treeview", font=("Segoe UI", 9), rowheight=26)
        st.configure("Treeview.Heading", background="#123B45", foreground="white",
                     font=("Segoe UI", 9, "bold"))

    def interface(self):
        topo = tk.Frame(self, bg="#123B45", padx=15, pady=12)
        topo.pack(fill="x")
        self.logo_label = tk.Label(topo, text="LOGO DA EMPRESA", bg="#123B45",
                                   fg="white", width=16, height=4, relief="groove")
        self.logo_label.pack(side="left", padx=(0, 14))
        bloco = tk.Frame(topo, bg="#123B45")
        bloco.pack(side="left", fill="x", expand=True)
        tk.Label(bloco, text="HISTÓRICO DE CONTATOS DE CLIENTES",
                 bg="#123B45", fg="white", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(bloco, text="Registro de atendimentos e consulta de histórico",
                 bg="#123B45", fg="#DCE9EB", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Button(topo, text="Inserir logo", command=self.selecionar_logo,
                  bg="white", fg="#123B45", relief="flat", padx=10, pady=7).pack(side="right")

        form = ttk.LabelFrame(self, text="Registrar contato", padding=10)
        form.pack(fill="x", padx=14, pady=10)
        for col in (1, 3, 5): form.columnconfigure(col, weight=1)
        self.campo(form, "Nome do cliente *", self.nome, 0, 0)
        self.campo(form, "Código do cliente", self.codigo, 0, 2)
        self.campo(form, "Telefone", self.telefone, 0, 4)

        ttk.Label(form, text="Projeto").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=self.projeto, values=["21", "22", "Outro"],
                     state="readonly", width=18).grid(row=1, column=1, sticky="ew")
        ttk.Label(form, text="Canal").grid(row=1, column=2, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=self.canal,
                     values=["WhatsApp", "Telefone", "E-mail", "Presencial", "Outro"],
                     state="readonly").grid(row=1, column=3, sticky="ew")
        ttk.Label(form, text="Assunto").grid(row=1, column=4, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=self.assunto, values=[
            "Cobrança", "Boleto", "INCC", "Parcelas vencidas", "Renegociação",
            "Negativação", "Baixa bancária", "Taxa de evolução de obra",
            "Cadastro", "Outros"]).grid(row=1, column=5, sticky="ew")

        ttk.Label(form, text="Relato do contato *").grid(row=2, column=0, sticky="nw", pady=4)
        self.relato = tk.Text(form, height=3, wrap="word", font=("Segoe UI", 10))
        self.relato.grid(row=2, column=1, columnspan=5, sticky="ew", pady=4)
        ttk.Label(form, text="Providência / retorno").grid(row=3, column=0, sticky="nw", pady=4)
        self.providencia = tk.Text(form, height=2, wrap="word", font=("Segoe UI", 10))
        self.providencia.grid(row=3, column=1, columnspan=5, sticky="ew", pady=4)
        self.campo(form, "Responsável", self.responsavel, 4, 0)

        ttk.Label(form, text="Anexos").grid(row=5, column=0, sticky="w", pady=5)
        self.anexos_label = ttk.Label(form, text="Nenhum arquivo anexado")
        self.anexos_label.grid(row=5, column=1, columnspan=3, sticky="w", pady=5)
        ttk.Button(form, text="Adicionar arquivo(s)", command=self.adicionar_anexos).grid(
            row=5, column=4, sticky="e", padx=3, pady=5)
        ttk.Button(form, text="Limpar anexos", command=self.limpar_anexos).grid(
            row=5, column=5, sticky="w", padx=3, pady=5)

        botoes = ttk.Frame(form)
        botoes.grid(row=6, column=1, columnspan=5, sticky="e", pady=6)
        ttk.Button(botoes, text="Limpar formulário", command=self.limpar).pack(side="left", padx=4)
        tk.Button(botoes, text="Salvar contato", command=self.salvar,
                  bg="#18A58A", fg="white", relief="flat", padx=14, pady=6,
                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)

        area = ttk.LabelFrame(self, text="Consultar histórico", padding=9)
        area.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        barra = ttk.Frame(area)
        barra.pack(fill="x", pady=(0, 8))
        ttk.Label(barra, text="Pesquisar nome, código, telefone ou assunto:").pack(side="left")
        entrada = ttk.Entry(barra, textvariable=self.busca, width=34)
        entrada.pack(side="left", padx=7)
        entrada.bind("<Return>", lambda e: self.listar())
        ttk.Button(barra, text="Pesquisar", command=self.listar).pack(side="left")
        ttk.Button(barra, text="Mostrar todos", command=self.todos).pack(side="left", padx=5)
        ttk.Button(barra, text="Exportar CSV", command=self.exportar).pack(side="right")

        cols = ("data", "cliente", "codigo", "telefone", "projeto", "assunto", "canal", "responsavel")
        self.tabela = ttk.Treeview(area, columns=cols, show="headings", selectmode="browse")
        titulos = ["Data e hora", "Cliente", "Código", "Telefone", "Projeto", "Assunto", "Canal", "Responsável"]
        larguras = [130, 200, 90, 110, 65, 175, 95, 130]
        for c, t, w in zip(cols, titulos, larguras):
            self.tabela.heading(c, text=t)
            self.tabela.column(c, width=w, minwidth=55)
        self.tabela.pack(fill="both", expand=True)
        self.tabela.bind("<Double-1>", lambda e: self.detalhes())
        rodape = ttk.Frame(area)
        rodape.pack(fill="x", pady=(7, 0))
        ttk.Button(rodape, text="Ver detalhes / abrir anexos", command=self.detalhes).pack(side="left")
        ttk.Button(rodape, text="Excluir selecionado", command=self.excluir).pack(side="left", padx=8)
        self.status = ttk.Label(rodape, text="")
        self.status.pack(side="right")

    def campo(self, pai, texto, variavel, linha, coluna):
        ttk.Label(pai, text=texto).grid(row=linha, column=coluna, sticky="w", pady=4)
        ttk.Entry(pai, textvariable=variavel).grid(
            row=linha, column=coluna+1, sticky="ew", padx=(0, 10), pady=4)

    def selecionar_logo(self):
        caminho = filedialog.askopenfilename(title="Escolher logo",
            filetypes=[("Imagens PNG ou GIF", "*.png *.gif")])
        if not caminho: return
        try:
            imagem = tk.PhotoImage(file=caminho)
            fator = max(1, (imagem.width()+119)//120, (imagem.height()+59)//60)
            if fator > 1: imagem = imagem.subsample(fator, fator)
            self.logo = imagem
            self.logo_label.configure(image=self.logo, text="", width=120, height=60)
        except tk.TclError:
            messagebox.showerror("Formato não suportado", "Use uma imagem PNG ou GIF para a logo.")

    def adicionar_anexos(self):
        caminhos = filedialog.askopenfilenames(title="Selecionar documentos ou imagens")
        for caminho in caminhos:
            if caminho not in self.arquivos_anexados:
                self.arquivos_anexados.append(caminho)
        self.atualizar_anexos()

    def limpar_anexos(self):
        self.arquivos_anexados = []
        self.atualizar_anexos()

    def atualizar_anexos(self):
        nomes = [Path(a).name for a in self.arquivos_anexados]
        texto = "; ".join(nomes) if nomes else "Nenhum arquivo anexado"
        self.anexos_label.configure(text=texto if len(texto) < 95 else texto[:92]+"...")

    def salvar(self):
        cliente = self.nome.get().strip()
        relato = self.relato.get("1.0", "end").strip()
        if not cliente or not relato:
            messagebox.showwarning("Campos obrigatórios", "Preencha o nome do cliente e o relato.")
            return
        dados = (datetime.now().strftime("%d/%m/%Y %H:%M"), cliente,
                 self.codigo.get().strip(), self.telefone.get().strip(), self.projeto.get(),
                 self.canal.get(), self.assunto.get(), relato,
                 self.providencia.get("1.0", "end").strip(), self.responsavel.get().strip(),
                 "\n".join(self.arquivos_anexados))
        with conectar() as db:
            db.execute("""INSERT INTO contatos
                (data_hora, cliente, codigo, telefone, projeto, canal, assunto,
                 relato, providencia, responsavel, anexos)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?)""", dados)
        messagebox.showinfo("Salvo", "Contato registrado com sucesso.")
        self.limpar()
        self.listar()

    def listar(self):
        for item in self.tabela.get_children(): self.tabela.delete(item)
        termo = "%" + self.busca.get().strip() + "%"
        with conectar() as db:
            linhas = db.execute("""SELECT id, data_hora, cliente, codigo, telefone,
                projeto, assunto, canal, responsavel FROM contatos
                WHERE cliente LIKE ? OR codigo LIKE ? OR telefone LIKE ?
                OR assunto LIKE ? OR relato LIKE ? ORDER BY id DESC""",
                (termo, termo, termo, termo, termo)).fetchall()
        for linha in linhas:
            ident, *valores = linha
            self.tabela.insert("", "end", iid=str(ident), values=valores)
        self.status.configure(text=f"{len(linhas)} registro(s)")

    def todos(self):
        self.busca.set("")
        self.listar()

    def limpar(self):
        for variavel, valor in [(self.nome, ""), (self.codigo, ""), (self.telefone, ""),
            (self.projeto, "21"), (self.canal, "WhatsApp"), (self.assunto, "Cobrança"),
            (self.responsavel, "")]:
            variavel.set(valor)
        self.relato.delete("1.0", "end")
        self.providencia.delete("1.0", "end")
        self.limpar_anexos()

    def selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showwarning("Selecione", "Selecione um contato na tabela.")
            return None
        return int(selecao[0])

    def abrir_arquivo(self, caminho):
        if not Path(caminho).exists():
            messagebox.showwarning("Arquivo não encontrado",
                f"O arquivo não está mais nesse local:\n{caminho}")
            return
        try:
            if sys.platform.startswith("win"): os.startfile(caminho)
            elif sys.platform == "darwin": subprocess.Popen(["open", caminho])
            else: subprocess.Popen(["xdg-open", caminho])
        except Exception as erro:
            messagebox.showerror("Erro ao abrir arquivo", str(erro))

    def detalhes(self):
        ident = self.selecionado()
        if ident is None: return
        with conectar() as db:
            r = db.execute("""SELECT data_hora, cliente, codigo, telefone, projeto,
                canal, assunto, relato, providencia, responsavel, anexos
                FROM contatos WHERE id=?""", (ident,)).fetchone()
        janela = tk.Toplevel(self)
        janela.title(f"Detalhes do contato #{ident}")
        janela.geometry("720x650")
        quadro = ttk.Frame(janela, padding=14)
        quadro.pack(fill="both", expand=True)
        quadro.columnconfigure(1, weight=1)
        nomes = ["Data e hora", "Cliente", "Código", "Telefone", "Projeto", "Canal",
                 "Assunto", "Relato", "Providência / retorno", "Responsável", "Anexos"]
        anexos = [x for x in (r[10] or "").split("\n") if x.strip()]
        for i, (nome, valor) in enumerate(zip(nomes, r)):
            ttk.Label(quadro, text=nome+":", font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="nw", padx=(0, 10), pady=5)
            if nome in ("Relato", "Providência / retorno"):
                caixa = tk.Text(quadro, height=5 if nome == "Relato" else 3, wrap="word")
                caixa.insert("1.0", valor or "")
                caixa.configure(state="disabled")
                caixa.grid(row=i, column=1, sticky="ew", pady=5)
            elif nome == "Anexos":
                frame = ttk.Frame(quadro)
                frame.grid(row=i, column=1, sticky="ew", pady=5)
                if anexos:
                    lista = tk.Listbox(frame, height=min(5, len(anexos)), width=70)
                    for a in anexos: lista.insert("end", a)
                    lista.pack(fill="x")
                    def abrir_selecionado(l=lista):
                        escolha = l.curselection()
                        if escolha: self.abrir_arquivo(l.get(escolha[0]))
                        else: messagebox.showwarning("Selecione", "Selecione um anexo na lista.")
                    ttk.Button(frame, text="Abrir anexo selecionado",
                               command=abrir_selecionado).pack(anchor="e", pady=4)
                else:
                    ttk.Label(frame, text="Nenhum anexo").pack(anchor="w")
            else:
                ttk.Label(quadro, text=valor or "—", wraplength=480).grid(
                    row=i, column=1, sticky="w", pady=5)
        ttk.Button(quadro, text="Fechar", command=janela.destroy).grid(
            row=len(nomes), column=1, sticky="e", pady=8)

    def excluir(self):
        ident = self.selecionado()
        if ident is None: return
        if messagebox.askyesno("Confirmar exclusão",
            "Deseja excluir este registro? Esta ação não pode ser desfeita."):
            with conectar() as db: db.execute("DELETE FROM contatos WHERE id=?", (ident,))
            self.listar()

    def exportar(self):
        destino = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")], initialfile="historico_contatos.csv")
        if not destino: return
        with conectar() as db:
            linhas = db.execute("""SELECT id, data_hora, cliente, codigo, telefone,
                projeto, canal, assunto, relato, providencia, responsavel, anexos
                FROM contatos ORDER BY id DESC""").fetchall()
        with open(destino, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["ID", "Data e hora", "Cliente", "Código", "Telefone",
                "Projeto", "Canal", "Assunto", "Relato", "Providência", "Responsável", "Anexos"])
            escritor.writerows(linhas)
        messagebox.showinfo("Exportação concluída", f"CSV salvo em:\n{destino}")

if __name__ == "__main__":
    criar_banco()
    App().mainloop()
