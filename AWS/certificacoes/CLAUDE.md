# AWS/certificacoes — Preparação para certificações AWS

Simulados de prova voltados às **certificações oficiais da AWS**, separados das provas de módulo
porque cobrem o conteúdo no **formato e no escopo do exame real** (podem misturar assuntos de vários
módulos e incluir tópicos específicos de prova, como pilares do Well-Architected, planos de suporte, etc.).

## Certificações previstas

| Código | Certificação | Nível | Pasta |
|--------|--------------|-------|-------|
| CLF-C02 | AWS Certified Cloud Practitioner | Foundational | `clf-c02/` |
| SAA-C03 | AWS Certified Solutions Architect – Associate | Associate | `saa-c03/` (futuro) |
| SOA-C02 | AWS Certified SysOps Administrator – Associate | Associate | `soa-c02/` (futuro) |
| DVA-C02 | AWS Certified Developer – Associate | Associate | `dva-c02/` (futuro) |

Começamos pelo **CLF-C02**, que é a porta de entrada e casa com os primeiros módulos do curso.

## Como praticar (conduzido pelo Claude)
Usa o mesmo driver das provas — só muda o banco:
```bash
python3 AWS/apps/session.py start AWS/certificacoes/clf-c02/questions.json --id cert
python3 AWS/apps/session.py answer A --id cert
python3 AWS/apps/session.py status --id cert
```
**Aprovação alvo: 70%** (o exame real do CLF-C02 é ~700/1000). O Claude tira dúvidas e explica cada questão.

## Estrutura
```
certificacoes/
├── CLAUDE.md
└── clf-c02/
    └── questions.json    ← banco do simulado (cresce conforme o curso avança)
```

## Convenção
- Um banco por certificação; ele **cresce** conforme cobrimos mais módulos.
- Questões no estilo do exame (cenários, "qual a MELHOR opção"), com `feedbacks` por alternativa.
- Manter o mapeamento assunto→módulo em dia, para o aluno saber o que revisar quando errar.
