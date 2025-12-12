package main

import (
	"fmt"
	"log"
	"os"
	"regexp"
	"slices"
	"strings"

	"github.com/hashicorp/go-changelog"
)

var (
	allowedTypes    = loadLines("../allowed-types.txt")
	allowedPrefixes = loadLines("../allowed-prefixes.txt")
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run main.go <path-to-changelog-file>")
	}
	content, err := os.ReadFile(os.Args[1])
	if os.IsNotExist(err) {
		fmt.Printf("No changelog entry file found at: %s (this may be expected)\n", os.Args[1])
		return
	}
	if err != nil {
		log.Fatalf("Error reading changelog file: %v", err)
	}
	notes := changelog.NotesFromEntry(changelog.Entry{Body: string(content)})
	if len(notes) == 0 {
		log.Fatal("Error validating changelog: no changelog entry found")
	}
	var errors []string
	for i, note := range notes {
		if !slices.Contains(allowedTypes, note.Type) {
			errors = append(errors, fmt.Sprintf("Entry %d: Unknown changelog type '%s', please use only the configured changelog entry types %v", i+1, note.Type, allowedTypes))
		} else if err := validateFormat(note.Body); err != nil {
			errors = append(errors, fmt.Sprintf("Entry %d: %v", i+1, err))
		}
	}
	if len(errors) > 0 {
		log.Fatalf("Error validating changelog:\n  - %s", strings.Join(errors, "\n  - "))
	}
	fmt.Println("Changelog entry is valid")
}

func validateFormat(content string) error {
	colonIdx := -1
	for _, prefix := range allowedPrefixes {
		if strings.HasSuffix(prefix, "/") {
			if strings.HasPrefix(content, prefix) {
				if !regexp.MustCompile(`^` + regexp.QuoteMeta(prefix) + `\w+: .+$`).MatchString(content) {
					return fmt.Errorf("entry with prefix '%s' must have format '%s<word>: <sentence>'", prefix, prefix)
				}
				colonIdx = strings.Index(content, ": ")
				break
			}
		} else if strings.HasPrefix(content, prefix+":") {
			colonIdx = strings.Index(content, ": ")
			break
		}
	}
	var sentence string
	if colonIdx != -1 {
		sentence = content[colonIdx+2:]
	}
	if sentence == "" {
		return fmt.Errorf("entry must follow format '<prefix>: <sentence>' where prefix is one of: %v", allowedPrefixes)
	}
	if strings.Contains(sentence, "\n") {
		return fmt.Errorf("sentence must be single line")
	}
	if sentence != strings.TrimSpace(sentence) {
		return fmt.Errorf("sentence must not have leading or trailing whitespace")
	}
	if strings.HasSuffix(sentence, ".") {
		return fmt.Errorf("sentence must not end with a period")
	}
	return nil
}

func loadLines(path string) []string {
	content, err := os.ReadFile(path)
	if err != nil {
		log.Fatalf("Error reading %s: %v", path, err)
	}
	var lines []string
	for _, line := range strings.Split(string(content), "\n") {
		if line = strings.TrimSpace(line); line != "" {
			lines = append(lines, line)
		}
	}
	return lines
}
