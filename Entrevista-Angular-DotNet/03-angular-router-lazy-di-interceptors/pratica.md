# Prática — Simulação de entrevista (Módulo 03)

Estas são as perguntas que o agente usa para **simular o entrevistador** no chat. Ordem: da mais
comum à pegadinha. Para cada uma há uma **resposta-modelo** (o que um sênior diria, curta e direta) e
os **erros comuns** que derrubam o candidato. Regra da simulação: o aluno responde **sem olhar a
teoria**; o agente critica o que faltou e como soar mais sênior.

---

### Pergunta 1 — Como funciona o roteamento no Angular? Qual a diferença entre param de rota e query param?

**Resposta-modelo:** "O roteamento é definido por um array de `Routes` que mapeia cada `path` para um
componente ou um carregamento lazy; registro com `provideRouter(routes)` no bootstrap standalone. O
`<router-outlet>` é o placeholder onde a rota ativa renderiza, e rotas filhas usam um outlet aninhado.
Navego com `routerLink` no template ou `Router.navigate` no código. **Param de rota** (`user/:id`) é
parte obrigatória do caminho, lido pelo `paramMap`; **query param** (`?tab=x`) é opcional, lido pelo
`queryParamMap`. Uso `snapshot` quando o componente é recriado a cada navegação e **assino** o
Observable quando a URL muda sem recriar o componente."

**Erros comuns:** confundir param de rota com query param; dizer que sempre usa `snapshot` (falha
quando a mesma instância é reutilizada com id diferente); não citar `provideRouter`/standalone e falar
só de `RouterModule.forRoot` (versão antiga).

---

### Pergunta 2 — O que é lazy loading e por que usar?

**Resposta-modelo:** "Lazy loading adia o download do código de uma rota até o momento em que o usuário
navega até ela, usando um `import()` dinâmico. O bundler faz **code splitting** — gera *chunks*
separados — então o **bundle inicial fica menor** e a aplicação inicia mais rápido, o que melhora
o *first paint* e métricas como o tempo até interativo. Uso `loadComponent` para um componente
standalone e `loadChildren` para um grupo de rotas. O ganho é no carregamento **inicial**; o total
baixado ao longo da sessão é parecido com o eager."

**Erros comuns:** dizer que "deixa a app mais leve no total" (o ganho é no inicial, não no total);
não mencionar code splitting; não saber que `loadComponent` existe e citar só `loadChildren` com
`NgModule` (versão antiga).

---

### Pergunta 3 — Diferença entre loadChildren e loadComponent? E entre eager e lazy?

**Resposta-modelo:** "`loadComponent` carrega **um** componente standalone sob demanda; `loadChildren`
carrega um **conjunto** de rotas filhas (hoje apontando para um arquivo de rotas, não mais para um
`NgModule`). **Eager** é o padrão de uma rota com `component`: o código entra no bundle inicial e
carrega no boot. **Lazy** só baixa quando o usuário navega até a rota. Uso eager para o que é
essencial no início e lazy para telas pesadas ou pouco visitadas, como um painel de admin."

**Erros comuns:** trocar os dois; não saber que `loadChildren` pode apontar para um array de rotas
sem `NgModule`; achar que eager e preloading são a mesma coisa.

---

### Pergunta 4 — O que são preloading strategies? Diferença entre PreloadAllModules e NoPreloading?

**Resposta-modelo:** "Preloading baixa os chunks lazy em **segundo plano**, **depois** que a app já
inicializou, para que a próxima navegação seja instantânea — bundle inicial pequeno com navegação
rápida. `NoPreloading` é o padrão: nada em background, cada rota só baixa quando navego. `PreloadAllModules`
baixa todos os chunks lazy depois do boot. Também dá para escrever uma `PreloadingStrategy` customizada
que decide caso a caso, por exemplo só rotas marcadas com `data.preload`. Registro com
`withPreloading(...)` dentro do `provideRouter`."

**Erros comuns:** confundir preloading com eager (no preloading o código continua em chunk separado, só
muda **quando** baixa); não saber que existe estratégia customizada; não saber onde se registra.

---

### Pergunta 5 — Diferença entre CanActivate e CanMatch? Por que CanMatch é ótimo com lazy?

**Resposta-modelo:** "Ambos são guards funcionais que retornam `true`, um `UrlTree` (que redireciona)
ou um Observable disso. `CanActivate` roda **depois** que a rota casou — decide se ativa. `CanMatch`
roda **antes** do casamento; se falhar, o router **continua procurando** outra rota que case. Com uma
rota **lazy**, isso é decisivo: `CanActivate` já **baixa o chunk** antes de barrar, enquanto `CanMatch`
reprova **sem baixar** o chunk. Por isso, para proteger uma rota lazy — como uma área de admin — eu uso
`CanMatch`: economiza banda e não expõe o código protegido a quem não tem acesso."

**Erros comuns:** dizer que os dois são iguais; não saber que `CanActivate` baixa o chunk mesmo
reprovando; não citar `UrlTree` como forma de redirecionar.

---

### Pergunta 6 — O que é um resolver? Quando você usaria um?

**Resposta-modelo:** "Um resolver (`ResolveFn`) **pré-carrega dados antes** de a rota ser ativada, então
o componente já nasce com os dados prontos em `ActivatedRoute.data`. Uso quando quero evitar o 'flash'
de tela vazia enquanto o componente carrega e depois busca os dados — por exemplo, garantir que os dados
de um usuário já estejam disponíveis assim que a tela de detalhe abre. O trade-off é que a navegação
espera o resolver terminar, então ele deve ser rápido ou ter tratamento de erro para não travar a
navegação."

**Erros comuns:** confundir resolver com guard; não citar o trade-off (a navegação espera); não saber
que os dados chegam em `route.data`.

---

### Pergunta 7 — Como funciona a hierarquia de DI do Angular? O que é providedIn: 'root'?

**Resposta-modelo:** "O DI do Angular é **hierárquico**: quando um componente pede uma dependência, o
Angular busca **subindo** a árvore de injetores — componente → rota → root — até achar quem forneça.
`providedIn: 'root'` registra o service no **injetor raiz**: vira **singleton** na app inteira e, muito
importante, é **tree-shakable** — se ninguém injeta o service, o compilador o remove do bundle. Se eu
declaro um provider no nível do componente ou da rota, crio uma **instância própria** naquele escopo,
que **não** é o mesmo objeto do root."

**Erros comuns:** dizer que `providedIn: 'root'` é sempre "global e único" sem mencionar que providers
de escopo criam instâncias próprias; não saber do tree-shaking; não saber que a busca sobe a árvore.

---

### Pergunta 8 — Diferença entre inject() e injeção via constructor? Quando usar cada um?

**Resposta-modelo:** "As duas fazem a mesma coisa e usam o mesmo sistema de DI — é estilo. `inject()` é
a **API funcional** e é **obrigatória** em contextos que são funções, não classes: guards funcionais,
interceptors funcionais e resolvers. Também uso `inject()` em campos de classe por concisão. Constructor
injection é a forma clássica, ainda perfeitamente válida em componentes e services. Não há diferença de
comportamento em runtime."

**Erros comuns:** achar que `inject()` é "mais rápido" ou "mais moderno tecnicamente" (é só ergonomia);
não saber que em guards/interceptors funcionais **só** dá para usar `inject()`; achar que um substitui
o outro obrigatoriamente.

---

### Pergunta 9 — O que é um InjectionToken e por que ele existe?

**Resposta-modelo:** "Um `InjectionToken` é um token para injetar **valores que não são classes** —
configuração, uma string, uma função — com type-safety. Ele existe porque uma **interface** ou um
**tipo** somem em runtime (TypeScript é apagado na compilação), então não podem servir de chave de DI.
Com o token eu registro `{ provide: APP_CONFIG, useValue: {...} }` e injeto com `inject(APP_CONFIG)`.
Também é a base de **multi providers**: com `multi: true` posso registrar vários valores no mesmo token
e injetá-los como um array."

**Erros comuns:** tentar injetar uma interface diretamente (não funciona em runtime); não saber para que
serve o token; confundir com `providedIn`.

---

### Pergunta 10 — O que é um HTTP interceptor e quais os casos de uso?

**Resposta-modelo:** "Um interceptor funcional é uma `HttpInterceptorFn` `(req, next) => next(req)` que
intercepta **toda** requisição HTTP num **pipeline**: pode clonar/modificar a request na ida e observar
ou transformar a response na volta, tudo num só lugar — evita repetir lógica em cada chamada. Casos
clássicos: **anexar token de auth**, **tratamento de erro global** (por exemplo, 401 → mandar para o
login), **retry**, **logging** e **loading spinner**. Registro com
`provideHttpClient(withInterceptors([...]))`."

**Erros comuns:** não citar que é um pipeline; não lembrar dos casos de uso; falar da versão antiga por
classe com `HTTP_INTERCEPTORS` sem saber que o padrão moderno é funcional.

---

### Pergunta 11 — Como você adiciona um token de auth em todas as requisições?

**Resposta-modelo:** "Escrevo um interceptor funcional de auth. Dentro dele pego o token (via `inject()`
de um `AuthService`) e, como a `HttpRequest` é **imutável**, **clono** a request adicionando o header:
`req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })`, e passo o **clone** para o `next`.
Registro com `provideHttpClient(withInterceptors([authInterceptor]))`. Se não houver token, apenas
repasso `next(req)` sem modificar. Assim, toda requisição da app leva o header automaticamente, sem
repetir código."

**Erros comuns:** tentar mutar `req.headers` direto (a request é imutável — não funciona); esquecer de
passar o **clone** para o `next`; não tratar o caso sem token; não saber registrar com `withInterceptors`.

---

### Pergunta 12 — Se eu registro dois interceptors, em que ordem eles rodam? (pegadinha)

**Resposta-modelo:** "Eles formam um pipeline em cebola. Na **ida** (request), rodam **na ordem** do
array passado a `withInterceptors`; na **volta** (response), na **ordem inversa**. Então com
`[auth, error]`: na ida, `auth` roda primeiro (anexa o token), depois `error`; na volta, `error` recebe
a response primeiro (trata o 401), depois `auth`. Por isso a ordem importa — por exemplo, posicionar um
interceptor de retry antes ou depois do de erro muda completamente o comportamento. É um detalhe que
mostra que entendi o pipeline, não só que sei escrever um interceptor."

**Erros comuns:** achar que a ordem não importa; dizer que rodam na mesma ordem na ida e na volta (na
volta é invertida); não relacionar a ordem com casos reais como retry + erro.
