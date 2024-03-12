;;; flycheck-castep-linter.el --- Support castep-linter in flycheck

;; Copyright (C) 2024 Jacob Wilkins <jacob.wilkins@stfc.ac.uk>
;;
;; Author: Jacob Wilkins <jacob.wilkins@stfc.ac.uk>
;; Created: 09 Febuary 2024
;; Version: 1.0
;; Package-Requires: ((flycheck "0.18"))

;;; Commentary:

;; This package adds support for castep-linter to flycheck.  To use it, add
;; to your init.el:

;; (require 'flycheck-castep-linter)
;; (add-hook 'python-mode-hook 'flycheck-mode)

;;; License:

;; This file is not part of GNU Emacs.
;; However, it is distributed under the same license.

;; GNU Emacs is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 3, or (at your option)
;; any later version.

;; GNU Emacs is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with GNU Emacs; see the file COPYING.  If not, write to the
;; Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
;; Boston, MA 02110-1301, USA.

;;; Code:
(require 'flycheck)

(flycheck-def-args-var flycheck-castep-linter-args castep-linter)

(flycheck-define-checker castep-linter
  "castep-linter syntax checker. Requires castep-linter>=0.1.5

Customize `flycheck-castep-linter-args` to add specific args to default
executable.

See URL `https://pypi.org/project/castep-linter/'."

  :command ("castep-lint" "--format" "GCC"
            (eval flycheck-castep-linter-args)
            source-original)
  :error-patterns
  ((error line-start (file-name) ":" line ":" column ": Error:" (message) line-end)
   (warning line-start (file-name) ":" line ":" column ": Warning:" (message) line-end)
   (info line-start (file-name) ":" line ":" column ": Info:" (message) line-end))
  :modes f90-mode)

(add-to-list 'flycheck-checkers 'castep-linter t)

(provide 'flycheck-castep)
;;; flycheck-castep.el ends here
