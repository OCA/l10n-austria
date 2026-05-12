Once the POS is configured and assigned, every receipt closed at checkout is
automatically signed and the resulting QR code is printed at the bottom of the
receipt. Special receipts are produced when needed:

- **Startbeleg** – the very first signed receipt of a POS, stamped with the
  marker `STARTBELEG` on the printed receipt.
- **Nullbeleg** – manually triggered via the *Create Zero-Receipt* button on
  the POS configuration; printed with `NULLBELEG`.
- **Storno** – cancellation of a previous receipt, printed with `STORNO`.

The list and form views of *Point of Sale > Orders > Orders* expose the RKSV
fields (`a.sign Type`, `a.sign State`, `a.sign Sequence`, `a.sign Counter`,
`a.sign DEP`, `a.sign QR-Code`) for auditing and exporting the DEP.

Printable PDF reports are available for the certificate and the POS
configuration via the *Print* menu of the corresponding form.
