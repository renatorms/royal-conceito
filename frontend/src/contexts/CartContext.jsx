import { createContext, useContext, useEffect, useState } from "react";

const CartContext = createContext(null);
const STORAGE_KEY = "carrinho";

function carregarCarrinho() {
  try {
    const bruto = localStorage.getItem(STORAGE_KEY);
    return bruto ? JSON.parse(bruto) : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const [itens, setItens] = useState(carregarCarrinho);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(itens));
  }, [itens]);

  function adicionarItem(produto, variacao, quantidade = 1) {
    setItens((atual) => {
      const existente = atual.find((item) => item.variacaoId === variacao.id);

      if (existente) {
        const novaQuantidade = Math.min(existente.quantidade + quantidade, variacao.estoque);
        return atual.map((item) =>
          item.variacaoId === variacao.id
            ? { ...item, quantidade: novaQuantidade, estoque: variacao.estoque }
            : item
        );
      }

      return [
        ...atual,
        {
          itemId: variacao.id,
          produtoId: produto.id,
          produtoNome: produto.nome,
          marcaNome: produto.marca_nome,
          preco: produto.preco,
          variacaoId: variacao.id,
          tamanho: variacao.tamanho,
          estoque: variacao.estoque,
          quantidade: Math.min(quantidade, variacao.estoque),
        },
      ];
    });
  }

  function removerItem(itemId) {
    setItens((atual) => atual.filter((item) => item.itemId !== itemId));
  }

  // Quantidade abaixo de 1 remove o item — evita um estado "0 unidades" que
  // ainda ocupa uma linha no carrinho sem significado prático para o usuário.
  function atualizarQuantidade(itemId, novaQuantidade) {
    setItens((atual) => {
      if (novaQuantidade < 1) {
        return atual.filter((item) => item.itemId !== itemId);
      }

      return atual.map((item) =>
        item.itemId === itemId
          ? { ...item, quantidade: Math.min(novaQuantidade, item.estoque) }
          : item
      );
    });
  }

  function limparCarrinho() {
    setItens([]);
  }

  const totalItens = itens.reduce((soma, item) => soma + item.quantidade, 0);
  const totalValor = itens.reduce((soma, item) => soma + item.quantidade * Number(item.preco), 0);

  const value = {
    itens,
    adicionarItem,
    removerItem,
    atualizarQuantidade,
    limparCarrinho,
    totalItens,
    totalValor,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart deve ser usado dentro de um CartProvider");
  }
  return context;
}
