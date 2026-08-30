# Passo a passo — publicar o reúso no dados.gov.br

Baseado na página oficial **"Saiba como publicar um reúso"**
(<https://dados.gov.br/dados/conteudo/saiba-como-publicar-um-reuso>), consultada
em 30/08/2026. Os valores a digitar em cada campo estão em
`docs/publicacao-reuso.md`.

---

## 0. Antes de começar

1. **Deploy do painel** primeiro (`docs/deploy.md` — agora com o passo a passo
   do login no Streamlit Cloud e de como deixar o app público). O formulário
   pede a URL pública onde o reúso está hospedado — sem ela não há o que
   publicar. Estado do projeto: v1.4, pipeline completo, L1 completo, IEAS para
   921/925 município-anos.
2. Tenha em mãos: a URL do painel (`https://farol-ss.streamlit.app`), o link do
   repositório (<https://github.com/protazoarium/farol-ss>), uma **logo 1:1 de
   no mínimo 200×200 px** e **1 a 3 capturas de tela** do painel no mesmo
   formato (sugestão: mapa da página Farol, o diagrama do índice, a página
   Alertas ou Fontes).

---

## 1. Criar o perfil de consumidor

O reúso é publicado por um **usuário consumidor** (pessoa física) ou por um
**usuário de organização**. Para o concurso, use o **perfil de consumidor**.

1. Acesse <https://dados.gov.br> e clique em **"Entrar"** (canto superior direito).
2. Autentique-se com a **conta gov.br**.
3. No primeiro acesso o portal cria o **perfil de consumidor** automaticamente
   e leva você à *dashboard* (painel do usuário). Se pedir para completar o
   cadastro, preencha nome e e-mail de contato.

> A opção de organização só é necessária para órgãos/entidades e exige
> solicitação por e-mail a `dadosabertos@cgu.gov.br`. **Não use** para o
> concurso — para organização o reúso é publicado sem passar por homologação,
> o que não é o fluxo esperado aqui.

---

## 2. Abrir a tela de gestão de reúsos

1. Na *dashboard*, no **menu da esquerda**, clique em **"Reúsos"**.
2. Abre a tela de **gestão de reúsos** (lista dos seus reúsos, vazia no início).
3. Clique em **"Adicionar reúso"** (canto superior direito da lista).

---

## 3. Preencher o formulário de cadastro

Preencha ao menos os campos obrigatórios (marcados com asterisco). Dicionário
oficial dos campos, com os valores prontos, em `docs/publicacao-reuso.md`.
Resumo do que cada campo espera:

| Campo | Espera |
|---|---|
| **Nome** | nome do reúso por extenso |
| **URL** | endereço web onde o reúso está hospedado |
| **Descrição** | explicação breve, **máx. 255 caracteres** |
| **Tipos** | uma opção: Painel · matéria jornalística · aplicativo · outros → **Painel** |
| **Nome / Email do responsável** | responsável técnico |
| **Data de lançamento** | data em que o reúso ficou público |
| **Descontinuado** | só se o reúso saiu do ar (deixe em branco) |
| **Logo do reúso** | imagem 1:1, ≥ 200×200 px |
| **Telas do reúso** | 1–3 imagens 1:1, ≥ 200×200 px |
| **Organização/Autor** | preenchido automaticamente, não editável |
| **Conjunto de dados de origem** | conjuntos **catalogados no dados.gov.br** — o campo tem busca; adicione um a um |
| **Conjunto de dados não catalogados** | texto livre; separar por `;`, URL entre `( )` |
| **Temas** | um ou mais temas (Administração, Cultura, Saúde, …) → **Saúde** + Economia + Governo |
| **Palavras-chave** | termos que destacam o assunto |
| **Visibilidade** | **Pública** (senão o reúso não aparece para a sociedade) |

### Como preencher "Conjunto de dados de origem"

1. Clique no campo — abre uma busca sobre o catálogo do dados.gov.br.
2. Digite o nome do conjunto (ex.: `Sinan/Dengue`, `SIOPS`, `PNCP`,
   `Famílias Inscritas no Cadastro Único`) e selecione na lista.
3. Repita para cada conjunto. A lista completa está em
   `docs/publicacao-reuso.md`.

---

## 4. Salvar e enviar para homologação

1. Clique em **"Salvar"**. O reúso é criado com status **"Em edição"**.
2. Volte à lista de reúsos, abra o reúso recém-criado em **"Editar"**.
3. **Role até o fim da tela** — aparece o botão **"Enviar para homologação"**.
   Clique.
4. O reúso passa a **"Pendente de homologação"** e fica aguardando a
   **autorização da CGU** para ser exibido publicamente.

> Cuidado: **qualquer edição** de um reúso pendente ou já publicado devolve o
> status para "Em edição", e todo o processo de envio para homologação precisa
> ser refeito. Revise tudo antes de enviar.

---

## 5. Depois da homologação

- Assim que a CGU homologar, o reúso aparece na **Galeria de Reúsos** do portal
  e recebe uma **URL pública** (`dados.gov.br/dados/reuso/<id>`).
- Guarde essa URL: é o comprovante da Etapa 2 do concurso.
- Confira se os conjuntos de dados de origem aparecem linkados na página do
  reúso.

---

## Fluxo de status (resumo)

```
Em edição  ──"Salvar"──▶  Em edição
Em edição  ──"Enviar para homologação"──▶  Pendente de homologação
Pendente   ──CGU homologa──▶  Publicado (Galeria de Reúsos)
Publicado  ──qualquer "Editar"──▶  Em edição   (reenviar!)
```

---

## Links úteis

- Instruções oficiais: <https://dados.gov.br/dados/conteudo/saiba-como-publicar-um-reuso>
- Galeria de Reúsos: <https://dados.gov.br/dados/reusos>
- Formulário da CGU (Etapa 1): <https://formularios.cgu.gov.br/index.php/263319>
- Regras do concurso: `docs/concurso-cgu.md`
- Valores prontos para os campos: `docs/publicacao-reuso.md`
