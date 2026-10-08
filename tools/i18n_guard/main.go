package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strconv"
)

var sinkArgs = map[string][]int{
	"text":             {2},
	"drawPageHeader":   {2, 3},
	"drawDetailButton": {3},
	"drawActionCard":   {5, 6},
	"messageBox":       {1, 2},
	"appendTrayItem":   {2},
	"setTray":          {2},
}

var allowedVisibleLiterals = map[string]bool{
	"":  true,
	"×": true,
	"✓": true,
	"○": true,
	"!": true,
	"◆": true,
}

func callName(fun ast.Expr) string {
	switch x := fun.(type) {
	case *ast.Ident:
		return x.Name
	case *ast.SelectorExpr:
		return x.Sel.Name
	}
	return ""
}

func main() {
	root := "."
	if len(os.Args) > 1 {
		root = os.Args[1]
	}
	files := []string{"ui.go", "main.go", "engine.go", "history_export.go"}
	fset := token.NewFileSet()
	failed := false
	for _, name := range files {
		path := filepath.Join(root, name)
		f, err := parser.ParseFile(fset, path, nil, 0)
		if err != nil {
			fmt.Fprintf(os.Stderr, "parse %s: %v\n", path, err)
			os.Exit(2)
		}
		ast.Inspect(f, func(n ast.Node) bool {
			call, ok := n.(*ast.CallExpr)
			if !ok {
				return true
			}
			name := callName(call.Fun)
			positions, ok := sinkArgs[name]
			if !ok {
				return true
			}
			for _, pos := range positions {
				if pos >= len(call.Args) {
					continue
				}
				lit, ok := call.Args[pos].(*ast.BasicLit)
				if !ok || lit.Kind != token.STRING {
					continue
				}
				v, err := strconv.Unquote(lit.Value)
				if err != nil {
					continue
				}
				if allowedVisibleLiterals[v] {
					continue
				}
				p := fset.Position(lit.Pos())
				fmt.Printf("FAIL visible literal at %s:%d sink=%s value=%q\n", p.Filename, p.Line, name, v)
				failed = true
			}
			return true
		})
	}
	if failed {
		os.Exit(1)
	}
	fmt.Println("PASS: no presentation string literals in UI/tray/modal sinks")
}
