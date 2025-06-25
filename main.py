import numpy as np
import sys

class SimplexSolver:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.c, self.A, self.b, self.constraints_type = self._ler_arquivo()
        self.n_vars = self.A.shape[1]
        self.n_constraints = self.A.shape[0]
        self.tableau = None
        self.basis = None
        self.var_names = [f'x{i+1}' for i in range(self.n_vars)]

    def _ler_arquivo(self):
        with open(self.filepath, 'r') as f:
            lines = f.readlines()

        c = np.array([float(x) for x in lines[0].strip().split()])
        A_list, b_list, constraints_type = [], [], []
        for i in range(1, len(lines)):
            parts = lines[i].strip().split()
            A_list.append([float(x) for x in parts[:-2]])
            constraints_type.append(parts[-2])
            b_list.append(float(parts[-1]))

        return np.array(c), np.array(A_list), np.array(b_list), constraints_type

    def _inicializar_tableau(self):
        num_slacks = self.constraints_type.count('<=')
        num_surplus = self.constraints_type.count('>=')
        num_artificials = num_surplus

        # Montagem do tableau
        self.tableau = np.zeros((self.n_constraints + 1,
                                  1 + self.n_vars + num_slacks + num_surplus + num_artificials + 1))
        self.basis = [0] * self.n_constraints

        # Linha Z
        self.tableau[0, 1:self.n_vars+1] = -self.c
        self.tableau[0, 0] = 1

        # Preenche restrições
        row_idx = 1
        slack_idx = surplus_idx = artificial_idx = 0
        col_offset = self.n_vars + 1
        var_counter = self.n_vars

        for i in range(self.n_constraints):
            self.tableau[row_idx, 1:self.n_vars+1] = self.A[i]
            self.tableau[row_idx, -1] = self.b[i]

            if self.constraints_type[i] == '<=':
                self.tableau[row_idx, col_offset + slack_idx] = 1
                self.var_names.append(f'f{slack_idx+1}')
                self.basis[i] = var_counter
                var_counter += 1
                slack_idx += 1
            else:  # '>='
                self.tableau[row_idx, col_offset + num_slacks + surplus_idx] = -1
                self.var_names.append(f'e{surplus_idx+1}')
                var_counter += 1
                self.tableau[row_idx, col_offset + num_slacks + num_surplus + artificial_idx] = 1
                self.var_names.append(f'a{artificial_idx+1}')
                self.basis[i] = var_counter
                var_counter += 1
                surplus_idx += 1
                artificial_idx += 1

            row_idx += 1

        self.var_names.append('RHS')

        # Se houver artificiais, preparar Fase I
        if num_artificials > 0:
            # salva Z original
            self._original_z_row = self.tableau[0].copy()
            self._preparar_fase_1(num_slacks, num_surplus)

    def _preparar_fase_1(self, num_slacks, num_surplus):
        print("\n--- FASE I INICIADA ---")
        print("Problema auxiliar: Maximizar W = -Soma(variáveis artificiais)")

        # cria linha W no fim
        w_row = np.zeros(self.tableau.shape[1])
        w_row[0] = -1
        start_art_cols = 1 + self.n_vars + num_slacks + num_surplus
        w_row[start_art_cols:-1] = 1.0
        self.tableau = np.vstack([self.tableau, w_row])

        # zerar artificiais em W
        for i in range(self.n_constraints):
            if self.constraints_type[i] == '>=':
                self.tableau[-1] -= self.tableau[i+1]

        # swap Z <-> W (mantendo ambas)
        self.tableau[[0, -1]] = self.tableau[[-1, 0]]

    def _encontrar_coluna_pivo(self):
        obj = self.tableau[0, 1:-1]
        if np.all(obj >= -1e-9): return -1
        return np.argmin(obj) + 1

    def _encontrar_linha_pivo(self, col):
        rhs = self.tableau[1:, -1]
        col_vals = self.tableau[1:, col]
        ratios = np.full_like(rhs, np.inf)
        for i, v in enumerate(col_vals):
            if v > 1e-9:
                ratios[i] = rhs[i]/v
        if np.all(ratios == np.inf): return -1
        return np.argmin(ratios) + 1

    def _pivotear(self, linha, col):
        piv = self.tableau[linha, col]
        self.tableau[linha] /= piv
        for i in range(self.tableau.shape[0]):
            if i != linha:
                mult = self.tableau[i, col]
                self.tableau[i] -= mult * self.tableau[linha]
        self.basis[linha-1] = col-1

    def _resolver_simplex(self, fase: int):
        count = 1
        while True:
            print(f"\n--- Iteração {count} (Fase {fase}) ---")
            print(np.round(self.tableau,2))
            col = self._encontrar_coluna_pivo()
            if col == -1:
                print("\nCondição de otimalidade atingida.")
                return 'OTIMO'
            row = self._encontrar_linha_pivo(col)
            if row == -1:
                return 'ILIMITADO'
            print(f"Pivot: entrar col {col}, sair linha {row}")
            self._pivotear(row, col)
            count += 1

    def _extrair_solucao(self):
        sol, z = {}, self.tableau[0, -1]
        for i in range(self.n_vars):
            if i in self.basis:
                idx = self.basis.index(i)
                sol[f'x{i+1}'] = self.tableau[idx+1, -1]
            else:
                sol[f'x{i+1}'] = 0
        print("\n--- SOLUÇÃO ÓTIMA ---")
        for v, val in sol.items(): print(f"{v} = {val:.4f}")
        print(f"Z = {z:.4f}")
        return sol, z

    def _verificar_solucoes_multiplas(self):
        obj = self.tableau[0, 1:self.n_vars+1]
        non_basic = [i for i in range(self.n_vars) if i not in self.basis]
        for i in non_basic:
            if abs(obj[i]) < 1e-9:
                print("\n--- MÚLTIPLAS SOLUÇÕES ÓTIMAS DETECTADAS ---")
                col, row = i+1, self._encontrar_linha_pivo(i+1)
                if row != -1:
                    self._pivotear(row, col)
                    self._extrair_solucao()
                return

    def resolver(self):
        self._inicializar_tableau()
        num_art = sum(1 for n in self.var_names if n.startswith('a'))
        if num_art > 0:
            status1 = self._resolver_simplex(1)
            if self.tableau[0, -1] < -1e-9:
                print("Inviável após Fase I")
                return
            print("--- FIM FASE I ---")
            # restaurar Z original
            self.tableau[0] = self._original_z_row
            # remover linha W
            self.tableau = np.delete(self.tableau, -1, axis=0)
            # remover colunas artificiais
            start = 1 + self.n_vars + self.constraints_type.count('<=') + self.constraints_type.count('>=')
            self.tableau = np.delete(
                self.tableau,
                np.s_[start:start+num_art],
                axis=1
            )
        print("--- FASE II ---")
        status2 = self._resolver_simplex(2)
        if status2 == 'OTIMO':
            self._extrair_solucao()
            self._verificar_solucoes_multiplas()
        else:
            print("Problema ilimitado.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python simplex_solver.py <arquivo>")
        sys.exit(1)
    solver = SimplexSolver(sys.argv[1])
    solver.resolver()
