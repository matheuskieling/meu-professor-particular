# AWS/certificacoes — Preparação para certificações AWS

Simulados voltados às **certificações oficiais da AWS**, separados das provas de módulo porque
cobrem o conteúdo no **formato e no escopo do exame real** (misturam assuntos de vários módulos e
incluem tópicos específicos de prova, como pilares do Well-Architected, planos de suporte, etc.).

## Certificações cobertas

| Código | Certificação | Nível | Formato do exame real | Pasta |
|--------|--------------|-------|-----------------------|-------|
| CLF-C02 | AWS Certified Cloud Practitioner | Foundational | 65 questões · 90 min · corte 700/1000 | `clf-c02/` |
| SAA-C03 | AWS Certified Solutions Architect – Associate | Associate | 65 questões · 130 min · corte 720/1000 | `saa-c03/` |
| SOA-C02 | AWS Certified SysOps Administrator – Associate | Associate | — | (futuro) |
| DVA-C02 | AWS Certified Developer – Associate | Associate | — | (futuro) |

## O que cada pasta contém

Cada certificação tem **dois tipos de material**:

1. **Banco rápido** (`questions.json`) — questões avulsas para treino no dia a dia, entre módulos.
   Bom para aquecer e revisar por tema. (CLF: 30 questões · SAA: 25 questões.)
2. **Provas completas** (`prova-1.json`, `prova-2.json`, `prova-3.json`) — **3 simulados fiéis ao
   exame real**: mesmas 65 questões, mesma distribuição de domínios do blueprint oficial, mesmo
   corte de aprovação, incluindo questões de **múltipla resposta** ("Escolha DUAS" — responda
   `answer A,C`). Faça-as **cronometradas** (90 min CLF / 130 min SAA) e **sem consulta**.

```
certificacoes/
├── CLAUDE.md
├── clf-c02/
│   ├── questions.json    ← banco rápido (30 questões)
│   ├── prova-1.json      ← simulado completo 1 (65 questões · 90 min · corte 70%)
│   ├── prova-2.json      ← simulado completo 2 (ênfase migração/governança/híbrido)
│   └── prova-3.json      ← simulado completo 3 (ênfase diferenciação de serviços/billing)
└── saa-c03/
    ├── questions.json    ← banco rápido (25 questões)
    ├── prova-1.json      ← simulado completo 1 (65 questões · 130 min · corte 72%)
    ├── prova-2.json      ← simulado completo 2 (ênfase dados/serverless/redes avançadas)
    └── prova-3.json      ← simulado completo 3 (ênfase migração/DR/custos)
```

## Como praticar (conduzido pelo Claude)

Mesmo driver das provas de módulo — só muda o banco:
```bash
# banco rápido (treino informal)
python3 AWS/apps/session.py start AWS/certificacoes/clf-c02/questions.json --id cert

# prova completa (simulado real: cronometrar e não consultar material!)
python3 AWS/apps/session.py start AWS/certificacoes/clf-c02/prova-1.json --id cert
python3 AWS/apps/session.py answer A --id cert        # resposta única
python3 AWS/apps/session.py answer A,C --id cert      # múltipla resposta ("Escolha DUAS")
python3 AWS/apps/session.py status --id cert
```

**Ao conduzir uma prova completa, o Claude deve:** anotar o horário de início e cobrar o limite de
tempo (90/130 min); não dar dicas durante a prova (feedback didático só depois de cada resposta,
como o driver já faz); ao final, registrar o resultado e **avaliar os portões de prontidão abaixo**,
dizendo explicitamente ao aluno se está pronto ou o que falta.

## 🎯 Portões de prontidão (quando o aluno está pronto)

### CLF-C02 (Cloud Practitioner)
| Portão | Critério |
|--------|----------|
| Pronto para os **simulados** | Módulos **01–07** concluídos com **≥70% em todas as provas de módulo** |
| Pronto para a **prova real** | **≥80% nas 3 provas completas**, cada uma em **até 90 min**, **sem consulta**, com os erros revisados depois |

### SAA-C03 (Solutions Architect – Associate)
| Portão | Critério |
|--------|----------|
| Pronto para os **simulados** | Módulos **01–18** concluídos com ≥70% nas provas de módulo |
| Pronto para a **prova real** | **≥80% nas 3 provas completas**, cada uma em **até 130 min**, sem consulta — e **Módulo 19 (projeto final)** concluído |

> **Por que 80% se o corte real é 70–72%?** No exame oficial há nervosismo, pressão de tempo e
> questões experimentais não pontuadas. Uma folga de ~10 pontos nos simulados é a margem de
> segurança padrão. Se ficar entre 70–79%: revise os domínios com mais erros e refaça a prova
> com pior nota antes de agendar o exame.

## Convenção
- Provas completas seguem o formato real: 65 questões, distribuição oficial por domínio, corte real,
  ~7-8 questões de múltipla resposta (`corretas: [i, j]`, 5 opções).
- Todas as questões têm `feedbacks` por alternativa (por que cada opção está certa/errada).
- Bancos rápidos podem crescer conforme o curso avança; as provas completas ficam estáveis
  (para permitir comparar tentativas).

## Próximas certificações (futuro)
Além de CLF-C02 e SAA-C03 (prontas), o curso vai cobrir DVA-C02, SOA-C02, DEA-C01, MLA-C01, AIF-C01,
SCS-C02, ANS-C01, SAP-C02 e DOP-C02 — cada uma como uma **trilha separada** (módulos próprios +
banco rápido + 3 provas). Plano completo em **`AWS/ROADMAP.md`**. Ainda não implementado.
