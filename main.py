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
        
        A_list = []
        b_list = []
        constraints_type = []

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

        self.tableau = np.zeros((self.n_constraints + 1, 1 + self.n_vars + num_slacks + num_surplus + num_artificials + 1))
        
        self.basis = [0] * self.n_constraints
        
        self.tableau[0, 1:self.n_vars + 1] = -self.c
        self.tableau[0, 0] = 1 
        
        row_idx = 1
        slack_idx = 0
        surplus_idx = 0
        artificial_idx = 0
        
        col_offset = self.n_vars + 1
        
        var_counter = self.n_vars
        
        for i in range(self.n_constraints):
            self.tableau[row_idx, 1:self.n_vars + 1] = self.A[i]
            self.tableau[row_idx, -1] = self.b[i]

            if self.constraints_type[i] == '<=':
                self.tableau[row_idx, col_offset + slack_idx] = 1
                self.var_names.append(f'f{slack_idx+1}')
                self.basis[i] = var_counter
                var_counter += 1
                slack_idx += 1
            elif self.constraints_type[i] == '>=':
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
        
        if num_artificials > 0:
            self._preparar_fase_1(num_slacks, num_surplus)

    def _preparar_fase_1(self, num_slacks, num_surplus):
        print("\n--- FASE I INICIADA ---")
        print("Problema auxiliar: Maximizar W = -Soma(variáveis artificiais)")

        w_row = np.zeros(self.tableau.shape[1])
        w_row[0] = -1 # Coeficiente de W
        
        start_artificial_cols = 1 + self.n_vars + num_slacks + num_surplus

        w_row[start_artificial_cols : -1] = 1.0
        
        self.tableau = np.vstack([self.tableau, w_row])
        
        for i in range(self.n_constraints):
            if self.constraints_type[i] == '>=':
                self.tableau[-1, :] -= self.tableau[i+1, :]
        
        self.tableau[[0, -1], :] = self.tableau[[-1, 0], :]
        self.tableau = np.delete(self.tableau, -1, axis=0)
        
    def _encontrar_coluna_pivo(self):
        obj_row = self.tableau[0, 1:-1]
        
        if np.all(obj_row >= -1e-9):
            return -1
            
        return np.argmin(obj_row) + 1

    def _encontrar_linha_pivo(self, col_pivo):
        rhs = self.tableau[1:, -1]
        pivo_col = self.tableau[1:, col_pivo]
        
        ratios = np.full_like(rhs, np.inf)
        
        for i in range(len(pivo_col)):
            if pivo_col[i] > 1e-9:
                ratios[i] = rhs[i] / pivo_col[i]
        
        if np.all(ratios == np.inf):
            return -1

        linha_pivo = np.argmin(ratios) + 1
        return linha_pivo

    def _pivotear(self, linha_pivo, col_pivo):
        pivo_element = self.tableau[linha_pivo, col_pivo]
        
        self.tableau[linha_pivo, :] /= pivo_element

        for i in range(self.tableau.shape[0]):
            if i != linha_pivo:
                multiplier = self.tableau[i, col_pivo]
                self.tableau[i, :] -= multiplier * self.tableau[linha_pivo, :]
        
        self.basis[linha_pivo - 1] = col_pivo - 1
        
    def _resolver_simplex(self, fase: int):
        iter_count = 1
        while True:
            print(f"\n--- Iteração {iter_count} (Fase {fase}) ---")
            print("Tableau Atual:")
            print(np.round(self.tableau, 2))
            
            col_pivo = self._encontrar_coluna_pivo()
            
            if col_pivo == -1:
                print("\nCondição de otimalidade atingida.")
                return "OTIMO"

            print(f"Variável a entrar na base (coluna pivô): {self.var_names[col_pivo-1]} (índice {col_pivo})")
            
            linha_pivo = self._encontrar_linha_pivo(col_pivo)
            
            if linha_pivo == -1:
                return "ILIMITADO"
            
            print(f"Variável a sair da base (linha pivô): {self.var_names[self.basis[linha_pivo-1]]} (índice {linha_pivo})")
            
            self._pivotear(linha_pivo, col_pivo)
            iter_count += 1
            
    def _extrair_solucao(self):
        solucao = {}
        valor_otimo = self.tableau[0, -1]
        
        for i in range(self.n_vars):
            var_name = f'x{i+1}'
            if i in self.basis:
                row_idx = self.basis.index(i)
                solucao[var_name] = self.tableau[row_idx + 1, -1]
            else:
                solucao[var_name] = 0
                
        print("\n--- SOLUÇÃO ÓTIMA ENCONTRADA ---")
        for var, val in solucao.items():
            print(f"{var} = {val:.4f}")
        print(f"Valor Ótimo (Z) = {valor_otimo:.4f}")
        
        return solucao, valor_otimo

    def _verificar_solucoes_multiplas(self):
        """Verifica e encontra soluções ótimas múltiplas se existirem."""
        obj_row = self.tableau[0, 1:self.n_vars + 1] # Apenas variáveis originais
        
        # Procura por variáveis não-básicas com custo reduzido zero
        non_basic_vars_idx = [i for i in range(self.n_vars) if i not in self.basis]
        
        for idx in non_basic_vars_idx:
            if abs(obj_row[idx]) < 1e-9:
                print(f"\n--- MÚLTIPLAS SOLUÇÕES ÓTIMAS DETECTADAS ---")
                print(f"Variável não-básica '{self.var_names[idx]}' tem custo reduzido zero.")
                print("Encontrando outra solução ótima...")
                
                col_pivo = idx + 1
                linha_pivo = self._encontrar_linha_pivo(col_pivo)
                
                if linha_pivo != -1:
                    self._pivotear(linha_pivo, col_pivo)
                    self._extrair_solucao()
                return

    def resolver(self):
        self._inicializar_tableau()

        num_artificials = sum(1 for name in self.var_names if name.startswith('a'))
        if num_artificials > 0:
            status_fase1 = self._resolver_simplex(fase=1)
            
            if self.tableau[0, -1] < -1e-9: 
                print("\n--- FIM FASE I ---")
                print(f"Valor ótimo da Fase I (W) é {self.tableau[0, -1]:.4f}.")
                print("Problema original é INVIÁVEL.")
                return
            
            print("\n--- FIM FASE I ---")
            print("Solução básica viável encontrada.")
            
            original_z_row = self.tableau[self.n_constraints + 1, :]
            self.tableau[0, :] = original_z_row
            
            self.tableau = np.delete(self.tableau, self.n_constraints + 1, axis=0)
            
            start_artificial_cols = 1 + self.n_vars + self.constraints_type.count('<=') + self.constraints_type.count('>=')
            self.tableau = np.delete(self.tableau, np.s_[start_artificial_cols : start_artificial_cols + num_artificials], axis=1)

            for i in range(len(self.basis)):
                basis_var_col = self.basis[i] + 1
                if self.tableau[0, basis_var_col] != 0:
                    multiplier = self.tableau[0, basis_var_col]
                    self.tableau[0, :] -= multiplier * self.tableau[i + 1, :]
            
        print("\n--- FASE II INICIADA ---")
        status = self._resolver_simplex(fase=2)
        
        if status == "OTIMO":
            self._extrair_solucao()
            self._verificar_solucoes_multiplas()
        elif status == "ILIMITADO":
            print("\n--- RESULTADO ---")
            print("O problema possui solução ILIMITADA.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python simplex_solver.py <caminho_para_o_arquivo_de_entrada>")
        sys.exit(1)
    
    arquivo_entrada = sys.argv[1]
    solver = SimplexSolver(arquivo_entrada)
    solver.resolver()