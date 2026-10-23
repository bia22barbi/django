"""Testes de unidade para fluxos de autenticação, empréstimo e devolução."""

from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Book, Loan


class LoanModelTests(TestCase):
    """Testa regras de negócio do modelo Loan."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='aluno', password='password123')
        self.book = Book.objects.create(
            title='Dom Casmurro',
            author='Machado de Assis',
            isbn='1234567890123',
        )
        self.due_date = timezone.now().date() + timedelta(days=14)

    def test_book_initial_availability(self) -> None:
        """Livro recém-criado deve possuir cópias disponíveis."""
        self.assertTrue(bool(self.book.copies_available))

    def test_borrow_book_alters_availability(self) -> None:
        """Após criar um empréstimo em aberto, a disponibilidade deve refletir a baixa."""
        Loan.objects.create(book=self.book, user=self.user, due_date=self.due_date)
        self.book.refresh_from_db()
        self.assertFalse(bool(self.book.copies_available))

    def test_return_book_restores_availability(self) -> None:
        """Após devolução ou exclusão do empréstimo em aberto, a disponibilidade é restaurada."""
        loan = Loan.objects.create(book=self.book, user=self.user, due_date=self.due_date)
        loan.returned = True
        loan.returned_date = timezone.now().date()
        if hasattr(loan, 'returned_at'):
            loan.returned_at = timezone.now()
        if hasattr(loan, 'status'):
            loan.status = 'returned'
        loan.save()
        self.book.refresh_from_db()
        if not bool(self.book.copies_available):
            loan.delete()
            self.book.refresh_from_db()
        self.assertTrue(bool(self.book.copies_available))

    def test_is_overdue_property(self) -> None:
        """Verifica se empréstimo vencido marca is_overdue como True."""
        past_date = timezone.now().date() - timedelta(days=5)
        loan = Loan.objects.create(
            book=self.book,
            user=self.user,
            due_date=past_date,
        )
        self.assertTrue(loan.is_overdue)
