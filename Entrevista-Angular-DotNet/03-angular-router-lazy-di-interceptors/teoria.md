# Módulo 03 — Angular: Router, Lazy Loading, DI & Interceptors

Este módulo cobre o **Router** do Angular e três temas que quase sempre caem em entrevista de nível
pleno/sênior: **lazy loading**, **injeção de dependência** e **HTTP interceptors**. O objetivo aqui
não é decorar sintaxe — é você conseguir **explicar em voz alta o porquê**: por que carregar código
sob demanda, por que `CanMatch` é melhor que `CanActivate` numa rota lazy, por que `providedIn:'root'`
é *tree-shakable*, e como anexar um token de autenticação em **todas** as requisições sem repetir
código.

Todo o conteúdo assume **Angular 17+/18**: apps *standalone* (sem `NgModule`), guards e interceptors
**funcionais**, `provideRouter(...)`, `provideHttpClient(withInterceptors(...))`, `inject()` e
`loadComponent`/`loadChildren`. Quando um tema tiver a versão "antiga" que o entrevistador pode citar
(ex.: interceptor por classe com `HTTP_INTERCEPTORS`), a nota aparece — mas o padrão do módulo é o
moderno.

---

## 1. Roteamento essencial: Routes, outlet, links, params e rotas filhas

O roteamento no Angular é definido por um array de **`Routes`**, onde cada rota mapeia um `path` para
um `component` (ou um carregamento lazy). No mundo standalone, você registra as rotas no bootstrap com
`provideRouter(routes)`.

O **`<router-outlet>`** é o *placeholder* no template: é ali que o Angular renderiza o componente da
rota ativa. Rotas filhas (`children`) renderizam num `<router-outlet>` **aninhado**, dentro do
template do componente-pai.

Navegação:
- **`routerLink`** — declarativa, no template: `<a [routerLink]="['/user', id]">`.
- **`Router.navigate(...)` / `navigateByUrl(...)`** — programática, no código.

Parâmetros:
- **Param de rota** (`path: 'user/:id'`) — parte do caminho, obrigatório para casar a rota. Lê-se via
  `ActivatedRoute.paramMap`.
- **Query param** (`?tab=perfil`) — opcional, não faz parte do casamento da rota. Lê-se via
  `queryParamMap`.

```typescript
// app.routes.ts
import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  {
    path: 'users',
    component: UsersComponent,
    children: [
      { path: '', component: UserListComponent },      // renderiza no outlet aninhado de UsersComponent
      { path: ':id', component: UserDetailComponent },
    ],
  },
  { path: '**', component: NotFoundComponent },         // curinga = 404
];
```

```typescript
// user-detail.component.ts — lendo param e queryParam
import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({ standalone: true, selector: 'app-user-detail', template: `...` })
export class UserDetailComponent {
  private route = inject(ActivatedRoute);

  // snapshot: bom quando o componente é recriado a cada navegação
  readonly idSnapshot = this.route.snapshot.paramMap.get('id');

  // observable: necessário quando a URL muda SEM recriar o componente (mesma rota, id diferente)
  readonly id$ = this.route.paramMap; // ...pipe(map(pm => pm.get('id')))
}
```

**Pegadinha:** `route.snapshot.paramMap` é capturado **uma vez**, na criação do componente. Se o
usuário navega de `/user/1` para `/user/2` e o Angular **reutiliza a mesma instância** do componente
(mesma rota, só o param muda), o snapshot **não atualiza** — você precisa **assinar** o Observable
`paramMap`. Isso derruba muito candidato.

**Como responder:** "Rotas são um array de objetos que mapeiam `path` para componente ou carregamento
lazy; o `<router-outlet>` é onde a rota ativa renderiza. Param de rota (`:id`) faz parte do caminho e
é obrigatório; query param (`?x=`) é opcional. Leio ambos pelo `ActivatedRoute` — uso `snapshot` quando
o componente é recriado a cada navegação e **assino** o `paramMap` quando a URL muda sem recriar o
componente."

---

## 2. Lazy loading: loadChildren, loadComponent e o ganho real de bundle

**Eager** (padrão para uma rota simples com `component`): o código do componente entra no **bundle
inicial** e é baixado no *boot* da aplicação. **Lazy**: o código só é baixado **quando o usuário
navega** até a rota.

O mecanismo é o **`import()` dinâmico**, que o bundler (esbuild no Angular moderno, antes o webpack)
usa para fazer **code splitting** — quebrar a aplicação em *chunks* separados. Resultado: o **bundle
inicial fica menor**, o *first paint* é mais rápido, e o resto vem sob demanda.

Duas formas no mundo standalone:

```typescript
// app.routes.ts
export const routes: Routes = [
  // Carrega UM componente standalone sob demanda
  {
    path: 'perfil',
    loadComponent: () =>
      import('./perfil/perfil.component').then((m) => m.PerfilComponent),
  },

  // Carrega um CONJUNTO de rotas filhas sob demanda (sem NgModule)
  {
    path: 'admin',
    loadChildren: () =>
      import('./admin/admin.routes').then((m) => m.ADMIN_ROUTES),
  },
];
```

```typescript
// admin/admin.routes.ts
import { Routes } from '@angular/router';
export const ADMIN_ROUTES: Routes = [
  { path: '', loadComponent: () => import('./dashboard.component').then((m) => m.DashboardComponent) },
  { path: 'users', loadComponent: () => import('./users.component').then((m) => m.UsersComponent) },
];
```

- **`loadComponent`** — lazy de um único componente standalone (novidade do Angular moderno).
- **`loadChildren`** — lazy de um grupo de rotas; hoje aponta para um arquivo de rotas
  (`ADMIN_ROUTES`), não mais para um `NgModule`.

**Pegadinha:** lazy loading **não reduz o total baixado** ao longo da sessão — se o usuário visitar
todas as telas, o volume total é parecido com o eager. O ganho é o **bundle inicial menor** e a
**percepção de velocidade** no primeiro carregamento. Dizer "lazy loading deixa a app mais leve no
total" é impreciso; o correto é "deixa o **carregamento inicial** mais rápido".

**Como responder:** "Lazy loading adia o download do código de uma rota até o momento em que o usuário
navega até ela, usando `import()` dinâmico. O bundler faz *code splitting* e gera *chunks* separados,
então o **bundle inicial** fica menor e a app inicia mais rápido. Uso `loadComponent` para um componente
standalone e `loadChildren` para um grupo de rotas. O ganho é no carregamento **inicial**, não no total
baixado."

---

## 3. Preloading strategies: PreloadAllModules, NoPreloading e custom

**Preloading** é baixar os *chunks* lazy **em segundo plano**, **depois** que a aplicação inicial já
carregou — para que a navegação futura para essas rotas seja **instantânea**. É o melhor dos dois
mundos: bundle inicial pequeno (como lazy) + navegação rápida (como se fosse eager).

- **`NoPreloading`** (padrão) — nada é pré-carregado; cada rota lazy só baixa quando o usuário navega.
- **`PreloadAllModules`** — assim que a app termina de carregar, o Angular baixa **todos** os chunks
  lazy em background, um a um.
- **Custom `PreloadingStrategy`** — você decide caso a caso (ex.: pré-carregar só rotas marcadas com
  `data: { preload: true }`, ou só em conexões rápidas).

```typescript
// main.ts — registrando com provideRouter (standalone)
import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter, withPreloading, PreloadAllModules } from '@angular/router';

bootstrapApplication(AppComponent, {
  providers: [provideRouter(routes, withPreloading(PreloadAllModules))],
});
```

```typescript
// custom-preload.strategy.ts — só pré-carrega rotas com data.preload === true
import { Injectable } from '@angular/core';
import { PreloadingStrategy, Route } from '@angular/router';
import { Observable, of } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class SelectivePreload implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<unknown>): Observable<unknown> {
    return route.data?.['preload'] ? load() : of(null);
  }
}
// registro: withPreloading(SelectivePreload)
```

**Pegadinha:** preloading **não é** eager. Com eager, o código entra no **bundle inicial** e carrega
**junto** com a app. Com preloading, o código continua num **chunk separado** — a diferença é apenas
**quando** ele é baixado: **depois** do boot, em background. O bundle inicial continua pequeno.

**Como responder:** "Preloading baixa os chunks lazy em segundo plano depois que a app já inicializou,
para que a próxima navegação seja instantânea. `NoPreloading` é o padrão (nada em background),
`PreloadAllModules` baixa tudo depois do boot, e uma estratégia customizada decide caso a caso — por
exemplo, só rotas marcadas com `data.preload`. Registro com `withPreloading(...)` dentro do
`provideRouter`. É diferente de eager: o código continua em chunk separado, só muda **quando** baixa."

---

## 4. Guards funcionais: CanActivate, CanMatch, CanDeactivate e resolvers

**Guards** protegem rotas. No Angular moderno são **funções** (não classes), que retornam
`boolean | UrlTree | Observable<...> | Promise<...>` e usam **`inject()`** por dentro. Retornar um
**`UrlTree`** redireciona (ex.: mandar para `/login`).

- **`CanActivate` (`CanActivateFn`)** — roda **depois** que a rota casou. Decide se pode **ativar**.
  Clássico: "o usuário está logado?".
- **`CanMatch` (`CanMatchFn`)** — roda **antes** de a rota casar. Se falhar, o router **continua
  procurando** outra rota que case. É **excelente com lazy**: reprovando aqui, o Angular **nem baixa
  o chunk** da rota protegida.
- **`CanDeactivate` (`CanDeactivateFn`)** — barra a **saída** da rota. Clássico: "há alterações não
  salvas, deseja realmente sair?". Recebe a instância do componente atual.
- **Resolver (`ResolveFn`)** — pré-carrega **dados** **antes** de ativar a rota; o componente já nasce
  com os dados prontos em `ActivatedRoute.data`, evitando o "flash de tela vazia".

```typescript
// auth.guard.ts — CanActivateFn funcional
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  // retorna true, ou um UrlTree que redireciona pro login
  return auth.isLoggedIn() ? true : router.createUrlTree(['/login']);
};
```

```typescript
// app.routes.ts — CanMatch protegendo uma rota lazy (não baixa o chunk se reprovar)
{
  path: 'admin',
  canMatch: [adminGuard],
  loadChildren: () => import('./admin/admin.routes').then((m) => m.ADMIN_ROUTES),
}
```

```typescript
// user.resolver.ts — ResolveFn pré-carrega os dados antes de ativar
import { inject } from '@angular/core';
import { ResolveFn } from '@angular/router';
import { UserService } from './user.service';

export const userResolver: ResolveFn<User> = (route) =>
  inject(UserService).getById(route.paramMap.get('id')!);
// rota: { path: 'user/:id', component: UserDetail, resolve: { user: userResolver } }
// no componente: this.route.snapshot.data['user']
```

**Pegadinha:** com uma rota **lazy**, `CanActivate` já **baixa o chunk** antes de decidir barrar (a
rota casou, o chunk carregou, aí o guard reprova). **`CanMatch`** roda **antes** do casamento, então
reprova **sem baixar** o chunk. Por isso, para **proteger uma rota lazy**, o preferido é **`CanMatch`**
— economiza banda e não expõe o código protegido a quem não tem acesso.

**Como responder:** "Guards funcionais são funções que retornam `true`, um `UrlTree` (que redireciona)
ou um Observable disso. `CanActivate` roda depois que a rota casou; `CanMatch` roda antes e, se falhar,
o router tenta outra rota — por isso `CanMatch` é o melhor para proteger rota lazy: reprova **sem baixar
o chunk**. `CanDeactivate` barra a saída (ex.: form sujo). Um resolver pré-carrega dados antes de
ativar, então o componente já nasce com os dados prontos."

---

## 5. Injeção de dependência: injector hierárquico, providedIn root e tokens

O Angular tem um sistema de DI com **injetores hierárquicos**. Quando um componente pede uma
dependência, o Angular busca **subindo a árvore** de injetores até encontrar quem forneça:
**componente → rota (route-level `providers`) → root (app inteira)**.

- **`providedIn: 'root'`** — registra o service no **injetor raiz**: é **singleton** na app toda e,
  crucialmente, **tree-shakable** — se **ninguém** injeta o service, o compilador o **remove do bundle**.
- **Providers no nível da rota** (`providers: [...]` numa `Route`) ou **no componente** — criam uma
  **instância própria** naquele escopo. **Não** é o mesmo objeto do root.

**`InjectionToken`** cria um "token" para injetar **valores que não são classes** (config, string,
função) com *type-safety* — porque uma interface some em runtime e não pode ser usada como chave de DI.

**`inject()` vs constructor:** ambos funcionam. `inject()` é a API **funcional**, obrigatória em
guards/interceptors/resolvers (que são funções, não classes) e conveniente em campos de classe;
constructor injection é a forma clássica. Não há diferença de comportamento — é estilo.

**Multi providers** (`multi: true`) permitem **vários valores** no **mesmo token**, injetados como um
**array** — padrão de plugin/estratégia.

```typescript
// injection token para config
import { InjectionToken } from '@angular/core';
export interface AppConfig { apiUrl: string; }
export const APP_CONFIG = new InjectionToken<AppConfig>('app.config');

// registro (main.ts): { provide: APP_CONFIG, useValue: { apiUrl: '/api' } }

// service singleton, tree-shakable
import { Injectable, inject } from '@angular/core';
@Injectable({ providedIn: 'root' })
export class ApiService {
  private cfg = inject(APP_CONFIG);       // inject() em campo de classe
  private base = this.cfg.apiUrl;
}
```

**Pegadinha:** `providedIn: 'root'` é **singleton** na app inteira; mas um provider declarado
**no componente** ou **numa rota** cria uma **nova instância** naquele escopo — **não** é o mesmo
objeto do root. Trocar "singleton global" por "singleton do escopo" confunde candidato. E cuidado:
usar uma **interface** como token de DI não funciona (interface não existe em runtime) — por isso o
`InjectionToken`.

**Como responder:** "O DI do Angular é hierárquico: componente → rota → root; o injetor sobe a árvore
até achar o provider. `providedIn: 'root'` registra no injetor raiz — singleton na app e *tree-shakable*
(sai do bundle se ninguém usar). Para injetar valores que não são classes, uso `InjectionToken`.
`inject()` é a API funcional (obrigatória em guards/interceptors); constructor injection é a clássica.
E `multi: true` permite vários valores no mesmo token, injetados como array."

---

## 6. HTTP Interceptors funcionais: pipeline, casos de uso e ordem

Um **interceptor funcional** é uma **`HttpInterceptorFn`** — uma função `(req, next) => next(req)` que
intercepta **toda requisição HTTP** num **pipeline**. Ela pode **clonar/modificar** a requisição na ida
e **observar/transformar** a resposta na volta, tudo num só lugar (DRY: não repetir lógica de auth/erro
em cada chamada).

Casos de uso clássicos (todos caem em entrevista):
- **Anexar token de auth** — adicionar `Authorization: Bearer ...` em toda requisição.
- **Tratamento de erro global** — `catchError` para tratar `401 → logout`, exibir toast, etc.
- **Retry** — reenviar requisições que falharam.
- **Logging** — logar cada request/response.
- **Loading spinner** — ligar/desligar um indicador global.

A `HttpRequest` é **imutável** — não dá pra editar direto; você **clona** com `req.clone(...)`.

```typescript
// auth.interceptor.ts — anexa o token de auth em TODA requisição
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).token;
  if (!token) return next(req);

  // req é imutável → clona adicionando o header
  const authReq = req.clone({
    setHeaders: { Authorization: `Bearer ${token}` },
  });
  return next(authReq);
};
```

```typescript
// error.interceptor.ts — tratamento de erro global (ex.: 401 -> login)
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) router.navigate(['/login']);
      // aqui poderia exibir um toast / logar
      return throwError(() => err);
    }),
  );
};
```

```typescript
// main.ts — registro funcional (a ORDEM do array importa)
import { provideHttpClient, withInterceptors } from '@angular/common/http';

bootstrapApplication(AppComponent, {
  providers: [
    provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
  ],
});
```

**Ordem de execução:** os interceptores rodam **na ordem do array** na **ida** (request), e na **ordem
inversa** na **volta** (response) — como uma cebola/pilha. Com `[auth, error]`: na ida, `auth` roda
primeiro (anexa o token) e depois `error`; na volta, `error` recebe a resposta primeiro (trata o
erro/401) e depois `auth`. Por isso a ordem em que você lista importa — ex.: um interceptor de retry
antes ou depois do de erro muda o comportamento.

> **Nota (versão antiga):** antes do Angular 15, o interceptor era uma **classe** que implementava
> `HttpInterceptor` e era registrada com o token multi `HTTP_INTERCEPTORS`. O entrevistador pode citar
> isso; o padrão moderno é o **funcional** com `withInterceptors`.

**Pegadinha:** a `HttpRequest` é **imutável** — se você tentar `req.headers.set(...)` esperando que a
requisição mude, não funciona; é preciso `req.clone({ setHeaders: {...} })` e passar o **clone** para o
`next`. Outra: esquecer que a **ordem** do array afeta o pipeline (ida na ordem, volta invertida).

**Como responder:** "Um interceptor funcional é uma `HttpInterceptorFn` `(req, next) => next(req)` que
intercepta toda requisição HTTP num pipeline — clona/modifica a request na ida e observa a response na
volta. Casos clássicos: anexar token de auth, tratamento de erro global (401→login), retry, logging,
loading spinner. Para anexar o token, clono a request com `req.clone({ setHeaders: { Authorization:
'Bearer ...' } })` porque ela é imutável. Registro com `provideHttpClient(withInterceptors([...]))` — e
a **ordem** do array importa: na ida roda na ordem, na volta na ordem inversa."

---

## Glossário

- **`Routes` / `provideRouter`** — array de rotas e a função que as registra no bootstrap standalone.
- **`<router-outlet>`** — placeholder onde o componente da rota ativa é renderizado; aninhado para rotas filhas.
- **Param de rota** (`:id`) — parte obrigatória do caminho; lido via `paramMap`. **Query param** (`?x=`) — opcional; lido via `queryParamMap`.
- **Lazy loading** — baixar o código de uma rota sob demanda via `import()` dinâmico (`loadComponent`/`loadChildren`).
- **Code splitting** — o bundler quebrar a app em *chunks* separados, reduzindo o bundle inicial.
- **Eager** — código no bundle inicial, carregado no boot. **Preloading** — baixar chunks lazy em background depois do boot.
- **`PreloadAllModules` / `NoPreloading`** — estratégias de preloading; a customizada implementa `PreloadingStrategy`.
- **`CanActivate`** — barra a ativação (depois de casar a rota). **`CanMatch`** — barra o casamento (antes); não baixa o chunk lazy se reprovar.
- **`CanDeactivate`** — barra a saída da rota. **Resolver (`ResolveFn`)** — pré-carrega dados antes de ativar.
- **`UrlTree`** — valor de retorno de guard que redireciona para outra rota.
- **Injetor hierárquico** — componente → rota → root; a busca sobe a árvore.
- **`providedIn: 'root'`** — service singleton na app e *tree-shakable*.
- **`InjectionToken`** — token para injetar valores que não são classes (config, funções) com type-safety.
- **`inject()`** — API funcional de DI (obrigatória em guards/interceptors). **Multi provider** (`multi:true`) — vários valores num token, injetados como array.
- **`HttpInterceptorFn`** — interceptor funcional `(req, next) => next(req)`; registrado com `withInterceptors(...)`.
- **`req.clone(...)`** — cria uma cópia modificada da request imutável (ex.: `setHeaders`).

## Checagem de entendimento

1. Qual a diferença entre um **param de rota** (`:id`) e um **query param** (`?tab=x`), e quando você usa `snapshot` em vez de assinar o `paramMap`?
2. O que é **lazy loading**, qual API você usa para carregar um componente standalone sob demanda, e por que o ganho é no bundle **inicial** (não no total baixado)?
3. Explique a diferença entre **eager**, **lazy sem preload** e **`PreloadAllModules`**.
4. Por que **`CanMatch`** é preferível a **`CanActivate`** para proteger uma **rota lazy**?
5. O que **`providedIn: 'root'`** faz, e por que ele é *tree-shakable*? Um provider no nível do componente gera o mesmo objeto singleton?
6. Como você **anexa um token de auth em todas as requisições** com um interceptor funcional, e por que precisa **clonar** a request? Em que **ordem** os interceptores rodam na ida e na volta?
